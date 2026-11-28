"""Verify staged pages and public image rendering before a legacy cutover."""

from __future__ import annotations

import argparse
import base64
import functools
import hashlib
import json
import os
import threading
import urllib.request
from datetime import UTC, datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin

from b2_image_hosting_test import NoRedirect, TestFailure
from legacy_image_migration import (
    PAGES_BASE,
    incremental_exclusion_files,
    read_inventory,
    source_bytes,
)

PLAN = Path(".github/legacy-image-cutover.json")
PLAN_VERSION = 2


def checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def source_sha1(repo: Path, image: dict) -> str:
    return hashlib.sha1(source_bytes(repo, image), usedforsecurity=False).hexdigest()


def request_id(plan: dict) -> str:
    return checksum(
        json.dumps(
            {key: value for key, value in plan.items() if key != "request_id"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )


def validate_plan(repo: Path, site: Path, plan: dict) -> dict[str, dict]:
    manifest = repo / ".github/legacy-image-migration.json"
    inventory = read_inventory(manifest)
    objects = {image["object_key"]: image for image in inventory["images"]}
    if (
        plan.get("schema_version") not in (1, PLAN_VERSION)
        or plan.get("phase") not in {"switch", "exclude"}
        or plan.get("manifest_sha256") != checksum(manifest.read_bytes())
        or plan.get("request_id") != request_id(plan)
        or not plan.get("documents")
        or not plan.get("images")
    ):
        raise TestFailure("Invalid cutover request")
    images = {}
    for image in plan["images"]:
        key = image["object_key"]
        if (
            key in images
            or key not in objects
            or any(
                image.get(field) != objects[key][field]
                for field in ("sha256", "bytes", "content_type", "url")
            )
        ):
            raise TestFailure("Invalid cutover image identity")
        if plan["schema_version"] == PLAN_VERSION and image.get("sha1") != source_sha1(
            repo, objects[key]
        ):
            raise TestFailure(f"The cutover SHA-1 differs from the original: {key}")
        images[key] = image
    for relative, document in plan["documents"].items():
        path = site / relative
        if (
            Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or any(part.startswith(".") for part in Path(relative).parts)
            or path.suffix != ".html"
            or not path.resolve().is_relative_to(site.resolve())
            or checksum(path.read_bytes()) != document["sha256"]
            or not set(document["images"]) <= images.keys()
        ):
            raise TestFailure("Staged article does not match the cutover request")
        if any(
            images[key]["url"] not in path.read_text() for key in document["images"]
        ):
            raise TestFailure("A staged article omits a migrated image")
    return images


def verify_exclusions(repo: Path, site: Path) -> None:
    path = repo / ".github/pages-excluded-assets.txt"
    if not path.exists() or not path.read_text().strip():
        return
    manifest = repo / ".github/legacy-image-migration.json"
    if not manifest.exists():
        raise TestFailure("Pages exclusions have no migration inventory")
    incremental_exclusion_files(repo, manifest, {}, protected_paths=set())
    for line in path.read_text().splitlines():
        if (site / line[1:]).exists():
            raise TestFailure("A selected legacy image remains in the Pages artifact")


def verify_browser(plan: dict, images: dict, base: str, output: Path) -> list[dict]:
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1800")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    if binary := os.environ.get("CHROME_BIN"):
        options.binary_location = binary
    browser = webdriver.Chrome(options=options)
    browser.set_page_load_timeout(60)
    browser.set_script_timeout(60)
    browser.execute_cdp_cmd(
        "Network.enable",
        {"maxTotalBufferSize": 100_000_000, "maxResourceBufferSize": 32_000_000},
    )
    results = []
    verified = set()
    try:
        for index, (relative, document) in enumerate(plan["documents"].items()):
            url = urljoin(base, relative)
            browser.get(url)
            height = browser.execute_script("return document.body.scrollHeight")
            for position in range(0, int(height), 800):
                browser.execute_script("scrollTo(0,arguments[0])", position)
            expected = [images[key]["url"] for key in document["images"]]
            WebDriverWait(browser, 45).until(
                lambda driver, expected=expected: driver.execute_script(
                    """
                    return [...document.images].filter(image =>
                      arguments[0].includes(image.currentSrc.split('#')[0]))
                      .every(image => image.complete && image.naturalWidth > 0);
                    """,
                    expected,
                )
            )
            decoded = browser.execute_async_script(
                """
                const finish = arguments[arguments.length - 1];
                Promise.all(arguments[0].map(url => new Promise(resolve => {
                  const image = new Image();
                  image.onload = () => resolve({
                    url, width: image.naturalWidth, height: image.naturalHeight
                  });
                  image.onerror = () => resolve({url, width: 0, height: 0});
                  image.src = url;
                }))).then(finish);
                """,
                expected,
            )
            if any(image["width"] <= 0 or image["height"] <= 0 for image in decoded):
                raise TestFailure("A migrated image cannot render in Chrome")
            expected_by_url = {image["url"]: image for image in images.values()}
            for entry in browser.get_log("performance"):
                message = json.loads(entry["message"])["message"]
                if message["method"] != "Network.responseReceived":
                    continue
                response = message["params"]["response"]
                image = expected_by_url.get(response["url"])
                if image is None or image["object_key"] in verified:
                    continue
                body = browser.execute_cdp_cmd(
                    "Network.getResponseBody",
                    {"requestId": message["params"]["requestId"]},
                )
                content = (
                    base64.b64decode(body["body"])
                    if body["base64Encoded"]
                    else body["body"].encode()
                )
                if (
                    response["status"] != 200
                    or response["mimeType"] != image["content_type"]
                    or len(content) != image["bytes"]
                    or checksum(content) != image["sha256"]
                ):
                    raise TestFailure("Rendered B2 bytes do not match the image")
                verified.add(image["object_key"])
            browser.execute_script("scrollTo(0,0)")
            if index < 3:
                browser.save_screenshot(str(output / f"page-{index + 1}.png"))
            results.append({"path": relative, "decoded_images": decoded})
    finally:
        browser.quit()
    if verified != images.keys():
        raise TestFailure("Chrome did not verify every migrated image response")
    return results


def expected_head_headers(image: dict) -> dict:
    return {
        "Content-Length": str(image["bytes"]),
        "Content-Type": image["content_type"],
        "X-Bz-Content-Sha1": image["sha1"],
    }


def verify_image_head(opener, image: dict) -> dict:
    request = urllib.request.Request(image["url"], method="HEAD")
    expected = expected_head_headers(image)
    with opener.open(request, timeout=30) as response:
        if response.status != 200:
            raise TestFailure(f"HTTP {response.status} for {image['url']}")
        headers = {name: response.headers.get(name) for name in expected}
    for name, value in expected.items():
        if headers[name] != value:
            raise TestFailure(f"{name} differs from the original for {image['url']}")
    return headers


def verify(repo: Path, site: Path, output: Path) -> dict:
    verify_exclusions(repo, site)
    plan = json.loads((repo / PLAN).read_text())
    images = validate_plan(repo, site, plan)
    if plan["budget_date"] != datetime.now(UTC).date().isoformat():
        raise TestFailure("The cutover request has no allowance for this UTC day")
    output.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(NoRedirect())
    result = {
        "schema_version": plan["schema_version"],
        "request_id": plan["request_id"],
        "phase": plan["phase"],
        "verified_at": datetime.now(UTC).isoformat(),
        "images": list(images.values()),
    }
    if plan["phase"] == "exclude":
        live_pages = {}
        for relative, document in plan["documents"].items():
            with opener.open(urljoin(PAGES_BASE, relative), timeout=30) as response:
                digest = checksum(response.read(10 * 1024 * 1024 + 1))
                if response.status != 200 or digest != document["sha256"]:
                    raise TestFailure(
                        f"The live page differs from its source: {relative}"
                    )
                live_pages[relative] = digest
        if plan["schema_version"] == PLAN_VERSION:
            result["live_pages"] = live_pages
            result["head_images"] = {
                image["url"]: verify_image_head(opener, image)
                for image in images.values()
            }
        else:
            result["pages"] = verify_browser(plan, images, PAGES_BASE, output)
    else:
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            functools.partial(SimpleHTTPRequestHandler, directory=str(site)),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result["staged_pages"] = verify_browser(
                plan, images, f"http://127.0.0.1:{server.server_port}/", output
            )
        finally:
            server.shutdown()
            server.server_close()
    validate_receipt(plan, result)
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def validate_receipt(plan: dict, result: dict) -> None:
    if (
        plan["schema_version"] not in (1, PLAN_VERSION)
        or result.get("schema_version") != plan["schema_version"]
        or result.get("request_id") != plan["request_id"]
        or result.get("phase") != plan["phase"]
        or result.get("images") != plan["images"]
    ):
        raise TestFailure("Verification receipt does not match the cutover")
    if plan["schema_version"] == PLAN_VERSION and plan["phase"] == "exclude":
        if result.get("live_pages") != {
            path: page["sha256"] for path, page in plan["documents"].items()
        }:
            raise TestFailure("HTTP verification omits or changes a live page")
        if result.get("head_images") != {
            image["url"]: expected_head_headers(image) for image in plan["images"]
        }:
            raise TestFailure("HTTP verification omits or changes an image header")
        return
    field = "pages" if plan["phase"] == "exclude" else "staged_pages"
    pages = result.get(field, [])
    images = {image["object_key"]: image["url"] for image in plan["images"]}
    if (
        not isinstance(pages, list)
        or len(pages) != len(plan["documents"])
        or {page.get("path") for page in pages} != plan["documents"].keys()
    ):
        raise TestFailure("Browser verification omits a migrated page")
    for page in pages:
        expected = {images[key] for key in plan["documents"][page["path"]]["images"]}
        decoded = page.get("decoded_images", [])
        if (
            len(decoded) != len(expected)
            or {image.get("url") for image in decoded} != expected
            or any(
                type(image.get(dimension)) is not int or image[dimension] <= 0
                for image in decoded
                for dimension in ("width", "height")
            )
        ):
            raise TestFailure("Browser verification omits a rendered image")


def verify_cached(repo: Path, site: Path, receipt: Path) -> None:
    verify_exclusions(repo, site)
    plan = json.loads((repo / PLAN).read_text())
    validate_plan(repo, site, plan)
    result = json.loads(receipt.read_text())
    validate_receipt(plan, result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--cached", type=Path)
    args = parser.parse_args()
    if args.static_only:
        verify_exclusions(args.repo, args.site)
        return
    if args.cached:
        verify_cached(args.repo, args.site, args.cached)
        return
    if args.output is None:
        parser.error("--output is required for cutover verification")
    try:
        result = verify(args.repo, args.site, args.output)
    except Exception:
        args.output.mkdir(parents=True, exist_ok=True)
        plan = json.loads((args.repo / PLAN).read_text())
        (args.output / "failure.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "request_id": plan.get("request_id"),
                    "verification_failed": True,
                }
            )
            + "\n"
        )
        raise
    print(json.dumps({"request_id": result["request_id"], "verified": True}))


if __name__ == "__main__":
    main()
