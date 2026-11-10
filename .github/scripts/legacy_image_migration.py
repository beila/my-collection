"""Migrate existing public image files without changing repository originals."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlsplit

from b2_image_hosting_test import B2, MAX_BYTES, TestFailure
from b2_image_upload import CONTENT_TYPES, object_key

PUBLIC_BASE = "https://f003.backblazeb2.com/file/my-collection-images/"
PAGES_BASE = "https://beila.github.io/my-collection/"
SOURCE_DIRECTORIES = frozenset({"facebook-instapaper", "nasica-blog"})
ATTRIBUTE = re.compile(
    r"""(?P<prefix>\b(?:src|href|xlink:href|poster|data-src|data-original|data-lazy-src|srcset)\s*=\s*)"""
    r"""(?P<quote>["'])(?P<value>.*?)(?P=quote)""",
    re.IGNORECASE | re.DOTALL,
)
CSS_URL = re.compile(
    r"""url\(\s*(?P<quote>["']?)(?P<value>[^"'()]*?)(?P=quote)\s*\)""",
    re.IGNORECASE,
)


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def read_inventory(path: Path, expected_hash: str | None = None) -> dict:
    content = path.read_bytes()
    if expected_hash is not None and digest(content) != expected_hash:
        raise TestFailure("Legacy inventory checksum mismatch")
    inventory = json.loads(content)
    if inventory.get("schema_version") != 1 or not inventory.get("images"):
        raise TestFailure("Invalid legacy image inventory")
    paths = set()
    objects = {}
    for image in inventory["images"]:
        relative = PurePosixPath(image["original_path"])
        extension = relative.suffix.lower()
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or len(relative.parts) < 2
            or relative.parts[0] not in SOURCE_DIRECTORIES
            or "\\" in str(relative)
            or str(relative) != image["original_path"]
            or str(relative) in paths
            or extension not in CONTENT_TYPES
            or not re.fullmatch(r"[0-9a-f]{64}", image["sha256"])
            or type(image["bytes"]) is not int
            or not 0 < image["bytes"] <= MAX_BYTES
            or image["content_type"] != CONTENT_TYPES[extension]
            or image["object_key"] != object_key(image["sha256"], extension)
            or image["path"] != image["object_key"]
            or image["url"] != PUBLIC_BASE + image["object_key"]
        ):
            raise TestFailure("Invalid legacy image identity")
        identity = (image["sha256"], image["bytes"], image["content_type"])
        previous = objects.setdefault(image["object_key"], identity)
        if previous != identity:
            raise TestFailure("Conflicting legacy image identity")
        paths.add(str(relative))
    return inventory


def source_bytes(repo: Path, image: dict) -> bytes:
    root = repo.resolve()
    source = (root / image["original_path"]).resolve()
    if not source.is_relative_to(root):
        raise TestFailure("Legacy image escapes its repository")
    with source.open("rb") as stream:
        content = stream.read(MAX_BYTES + 1)
    if len(content) != image["bytes"] or digest(content) != image["sha256"]:
        raise TestFailure(f"Legacy image changed: {image['original_path']}")
    return content


def upload_inventory(
    repo: Path,
    manifest: Path,
    expected_hash: str,
    receipt: Path,
    *,
    workers: int = 8,
    limit: int = 0,
    client_factory=B2,
) -> dict:
    inventory = read_inventory(manifest, expected_hash)
    if not 1 <= workers <= 8 or limit < 0:
        raise TestFailure("Invalid legacy upload limits")
    unique = {image["object_key"]: image for image in inventory["images"]}
    selected = sorted(unique.values(), key=lambda image: image["object_key"])
    if limit:
        selected = selected[:limit]
    local = threading.local()

    def transfer(image):
        content = source_bytes(repo, image)
        if not hasattr(local, "client"):
            local.client = client_factory()
        client = local.client
        if client.public_url(image) != image["url"]:
            raise TestFailure("Legacy image download endpoint changed")
        reused = client.verify(image)
        if not reused:
            client.upload(image, content)
            if not client.verify(image):
                raise TestFailure("Legacy image upload verification failed")
        return {
            key: image[key]
            for key in ("object_key", "sha256", "bytes", "content_type", "url")
        } | {"reused": reused}

    result = {
        "schema_version": 1,
        "manifest_sha256": expected_hash,
        "status": "partial",
        "expected_objects": len(selected),
        "images": [],
        "errors": [],
    }
    write_json(receipt, result)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {
            executor.submit(transfer, image): image["object_key"] for image in selected
        }
        for future in as_completed(pending):
            try:
                result["images"].append(future.result())
            except (OSError, ValueError, RuntimeError) as error:
                result["errors"].append(
                    {"object_key": pending[future], "error": str(error)}
                )
            if (len(result["images"]) + len(result["errors"])) % 25 == 0:
                write_json(receipt, result)
                print(
                    f"Verified {len(result['images'])}/{len(selected)} legacy images",
                    flush=True,
                )
    result["images"].sort(key=lambda image: image["object_key"])
    result["status"] = "failed" if result["errors"] else "verified"
    write_json(receipt, result)
    if result["errors"]:
        raise TestFailure(f"{len(result['errors'])} legacy image uploads failed")
    return result


def image_path(url: str, page_url: str) -> str | None:
    parsed = urlsplit(urljoin(page_url, html.unescape(url.strip())))
    if parsed.netloc != "beila.github.io" or not parsed.path.startswith(
        "/my-collection/"
    ):
        return None
    return unquote(parsed.path.removeprefix("/my-collection/"))


def rewrite_document(
    document: str, page_url: str, images: dict[str, dict]
) -> tuple[str, set[str]]:
    used = set()

    def replace_url(value):
        relative = image_path(value, page_url)
        if relative not in images:
            return value
        used.add(relative)
        fragment = urlsplit(html.unescape(value)).fragment
        return images[relative]["url"] + ("#" + fragment if fragment else "")

    def attribute(match):
        value = match["value"]
        if match["prefix"].strip().lower().startswith("srcset"):
            value = re.sub(
                r"(?<!\S)[^\s,]+",
                lambda token: replace_url(token[0]),
                value,
            )
        else:
            value = replace_url(value)
        return match["prefix"] + match["quote"] + value + match["quote"]

    rewritten = ATTRIBUTE.sub(attribute, document)

    def css(match):
        value = replace_url(match["value"])
        if value == match["value"]:
            return match[0]
        return f"url({match['quote']}{value}{match['quote']})"

    return CSS_URL.sub(css, rewritten), used


def collection_plan(repo: Path, manifest: Path, bookmarks: Path) -> dict:
    inventory = read_inventory(manifest)
    images = {image["original_path"]: image for image in inventory["images"]}
    saved = json.loads(bookmarks.read_text())
    bookmark_paths = {
        image_path(bookmark["url"], PAGES_BASE)
        for folder in saved["affected_folders"]
        for bookmark in folder["bookmarks"]
    }
    protected = set()
    documents = []
    for path in sorted(repo.rglob("*.html")):
        if any(part.startswith(".") for part in path.relative_to(repo).parts):
            continue
        relative = path.relative_to(repo).as_posix()
        document = path.read_text()
        rewritten, used = rewrite_document(
            document, urljoin(PAGES_BASE, relative), images
        )
        if relative in bookmark_paths:
            protected.update(used)
        if rewritten != document:
            documents.append(
                {
                    "path": relative,
                    "before_sha256": digest(document.encode()),
                    "after_sha256": digest(rewritten.encode()),
                    "images": sorted(used),
                    "saved": relative in bookmark_paths,
                }
            )
    return {
        "schema_version": 1,
        "manifest_sha256": digest(manifest.read_bytes()),
        "documents": documents,
        "protected_paths": sorted(protected),
        "protected_bytes": sum(images[path]["bytes"] for path in protected),
        "missing_saved_pages": sorted(
            path for path in bookmark_paths if path and not (repo / path).is_file()
        ),
    }


def capture_readers(
    manifest: Path, bookmarks: Path, output: Path, *, client_factory=None
) -> dict:
    if client_factory is None:
        from instapaper_adapter import InstapaperClient

        client_factory = InstapaperClient

    inventory = read_inventory(manifest)
    images = {image["original_path"]: image for image in inventory["images"]}
    saved = json.loads(bookmarks.read_text())
    candidates = {
        str(bookmark["bookmark_id"]): bookmark
        for folder in saved["affected_folders"]
        for bookmark in folder["bookmarks"]
    }
    if not all(identifier.isdigit() for identifier in candidates):
        raise TestFailure("Invalid saved bookmark identity")
    directory = output.parent / "readers"
    directory.mkdir(parents=True, exist_ok=True)
    local = threading.local()

    def capture(bookmark):
        if not hasattr(local, "client"):
            local.client = client_factory()
        document = local.client.get_text(bookmark["bookmark_id"])
        _rewritten, used = rewrite_document(document, bookmark["url"], images)
        destination = directory / f"{bookmark['bookmark_id']}.html"
        destination.write_text(document)
        destination.chmod(0o600)
        return {
            **bookmark,
            "status": "captured",
            "sha256": digest(document.encode()),
            "images": sorted(used),
        }

    result = {"schema_version": 1, "readers": [], "errors": []}
    with ThreadPoolExecutor(max_workers=4) as executor:
        pending = {
            executor.submit(capture, bookmark): bookmark
            for bookmark in candidates.values()
        }
        for future in as_completed(pending):
            try:
                result["readers"].append(future.result())
            except (OSError, ValueError, RuntimeError) as error:
                result["errors"].append(
                    pending[future] | {"status": "failed", "error": str(error)}
                )
            if (len(result["readers"]) + len(result["errors"])) % 25 == 0:
                write_json(output, result)
                print(f"Captured {len(result['readers'])} saved readers", flush=True)
    result["readers"].sort(key=lambda reader: reader["bookmark_id"])
    protected = {
        path for reader in result["readers"] for path in reader["images"]
    }
    result["protected_paths"] = sorted(protected)
    result["protected_bytes"] = sum(images[path]["bytes"] for path in protected)
    write_json(output, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("upload", "plan", "readers"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sha256")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bookmarks", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.operation == "upload":
        if not args.sha256:
            parser.error("upload requires --sha256")
        result = upload_inventory(
            args.repo,
            args.manifest,
            args.sha256,
            args.output,
            workers=args.workers,
            limit=args.limit,
        )
        print(json.dumps({"verified": len(result["images"])}))
    elif args.operation == "plan":
        if args.bookmarks is None:
            parser.error("plan requires --bookmarks")
        result = collection_plan(args.repo, args.manifest, args.bookmarks)
        write_json(args.output, result)
        print(
            json.dumps(
                {
                    "documents": len(result["documents"]),
                    "protected_images": len(result["protected_paths"]),
                    "protected_bytes": result["protected_bytes"],
                    "missing_saved_pages": len(result["missing_saved_pages"]),
                }
            )
        )
    else:
        if args.bookmarks is None:
            parser.error("readers requires --bookmarks")
        result = capture_readers(args.manifest, args.bookmarks, args.output)
        print(
            json.dumps(
                {
                    "captured": len(result["readers"]),
                    "failed": len(result["errors"]),
                    "protected_bytes": result["protected_bytes"],
                }
            )
        )


if __name__ == "__main__":
    main()
