"""Migrate existing public image files without changing repository originals."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, as_completed, wait
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urljoin, urlsplit

from b2_image_hosting_test import B2, MAX_BYTES, NoRedirect, TestFailure
from b2_image_upload import CONTENT_TYPES, object_key

PUBLIC_BASE = "https://f003.backblazeb2.com/file/my-collection-images/"
PAGES_BASE = "https://beila.github.io/my-collection/"
SOURCE_DIRECTORIES = frozenset({"facebook-instapaper", "nasica-blog"})
DAILY_IMAGES = 500
DAILY_READ_REQUESTS = 1000
DAILY_DOWNLOAD_BYTES = 100_000_000
DAILY_START = 23 * 3600 + 45 * 60
DAILY_END = 23 * 3600 + 58 * 60
ATTRIBUTE = re.compile(
    r"""(?P<prefix>\b(?:src|href|xlink:href|poster|data-src|data-original|data-lazy-src|srcset|content)\s*=\s*)"""
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


class MigrationPaused(TestFailure):
    pass


class DailyMigrationBudget:
    """Reserve migration reads before they use the shared account allowance."""

    def __init__(self, result, images, checkpoint, lock, *, clock=time.time):
        self.result = result
        self.images = {image["url"]: image for image in images.values()}
        self.checkpoint = checkpoint
        self.lock = lock
        self.clock = clock
        self.opener = urllib.request.build_opener(NoRedirect())
        day = datetime.fromtimestamp(clock(), UTC).date().isoformat()
        previous = result.get("daily_upload")
        if previous is not None:
            if (
                not isinstance(previous, dict)
                or not isinstance(previous.get("date"), str)
                or not isinstance(previous.get("objects"), list)
                or len(set(previous["objects"])) != len(previous["objects"])
                or not set(previous["objects"]) <= images.keys()
                or len(previous["objects"]) > DAILY_IMAGES
                or type(previous.get("read_requests")) is not int
                or not 0 <= previous["read_requests"] <= DAILY_READ_REQUESTS
                or type(previous.get("download_bytes")) is not int
                or not 0 <= previous["download_bytes"] <= DAILY_DOWNLOAD_BYTES
            ):
                raise TestFailure("Invalid daily migration checkpoint")
            try:
                datetime.strptime(previous["date"], "%Y-%m-%d")
            except ValueError as error:
                raise TestFailure("Invalid daily migration date") from error
            if previous["date"] > day:
                raise TestFailure("Daily migration checkpoint is from the future")
        self.state = (
            previous
            if previous is not None and previous["date"] == day
            else {
                "date": day,
                "objects": [],
                "read_requests": 0,
                "download_bytes": 0,
            }
        )
        result["daily_upload"] = self.state

    def deadline(self) -> float:
        now = datetime.fromtimestamp(self.clock(), UTC)
        seconds = now.hour * 3600 + now.minute * 60 + now.second
        if (
            now.date().isoformat() != self.state["date"]
            or not DAILY_START <= seconds < DAILY_END
        ):
            raise MigrationPaused("outside the 23:45–23:58 UTC migration window")
        return now.replace(hour=23, minute=58, second=0, microsecond=0).timestamp()

    def open(self, request, *, timeout=60):
        with self.lock:
            remaining = self.deadline() - self.clock()
            if remaining <= 0:
                raise MigrationPaused("daily migration window ended")
            url = request if isinstance(request, str) else request.full_url
            image = self.images.get(url)
            if image is not None:
                key = image["object_key"]
                if (
                    key not in self.state["objects"]
                    and len(self.state["objects"]) >= DAILY_IMAGES
                ):
                    raise MigrationPaused("daily migration image limit reached")
                if self.state["read_requests"] >= DAILY_READ_REQUESTS:
                    raise MigrationPaused("daily migration request limit reached")
                if self.state["download_bytes"] + image["bytes"] > DAILY_DOWNLOAD_BYTES:
                    raise MigrationPaused("daily migration byte limit reached")
                if key not in self.state["objects"]:
                    self.state["objects"].append(key)
                self.state["read_requests"] += 1
                self.state["download_bytes"] += image["bytes"]
                self.checkpoint()
        try:
            return self.opener.open(request, timeout=min(timeout, remaining))
        except urllib.error.HTTPError as error:
            if image is not None and error.code == 404:
                with self.lock:
                    self.state["download_bytes"] -= image["bytes"]
                    self.checkpoint()
            raise


def upload_inventory(
    repo: Path,
    manifest: Path,
    expected_hash: str,
    receipt: Path,
    *,
    workers: int = 8,
    limit: int = 0,
    resume_receipt: Path | None = None,
    daily: bool = False,
    clock=time.time,
    client_factory=B2,
) -> dict:
    inventory = read_inventory(manifest, expected_hash)
    if not 1 <= workers <= 8 or limit < 0 or (daily and limit):
        raise TestFailure("Invalid legacy upload limits")
    unique = {image["object_key"]: image for image in inventory["images"]}
    selected = sorted(unique.values(), key=lambda image: image["object_key"])
    if limit:
        selected = selected[:limit]
    expected_count = len(selected)
    prior = {}
    previous = {}
    if resume_receipt is not None:
        previous = json.loads(resume_receipt.read_text())
        if (
            previous.get("schema_version") != 1
            or previous.get("manifest_sha256") != expected_hash
            or previous.get("status") not in {"verified", "partial", "failed"}
        ):
            raise TestFailure("Resume receipt does not match the inventory")
        for record in previous.get("images", []):
            key = record.get("object_key")
            image = unique.get(key)
            fields = ("object_key", "sha256", "bytes", "content_type", "url")
            if (
                image is None
                or key in prior
                or any(record.get(field) != image[field] for field in fields)
            ):
                raise TestFailure("Resume receipt has an invalid image")
            prior[key] = {field: image[field] for field in fields} | {"reused": True}
    reused = []
    for image in selected:
        if image["object_key"] in prior:
            source_bytes(repo, image)
            reused.append(prior[image["object_key"]])
    selected = [image for image in selected if image["object_key"] not in prior]
    local = threading.local()
    lock = threading.RLock()
    result = {
        "schema_version": 1,
        "manifest_sha256": expected_hash,
        "status": "partial",
        "expected_objects": expected_count,
        "images": reused,
        "errors": [],
        "unattempted_objects": expected_count - len(reused),
    }

    def checkpoint():
        with lock:
            write_json(receipt, result)

    budget = None
    if daily:
        if "daily_upload" in previous:
            result["daily_upload"] = previous["daily_upload"]
        budget = DailyMigrationBudget(result, unique, checkpoint, lock, clock=clock)
        if not selected:
            result["status"] = "verified"
            checkpoint()
            return result
        try:
            budget.deadline()
        except MigrationPaused as error:
            result["pause_reason"] = str(error)
            checkpoint()
            return result

    def transfer(image):
        content = source_bytes(repo, image)
        if not hasattr(local, "client"):
            local.client = client_factory(opener=budget) if budget else client_factory()
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

    checkpoint()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {}
        remaining = iter(selected)

        def submit_next():
            image = next(remaining, None)
            if image is not None:
                pending[executor.submit(transfer, image)] = image["object_key"]

        for _ in range(workers):
            submit_next()
        stopped = False
        while pending:
            finished, _unfinished = wait(pending, return_when=FIRST_COMPLETED)
            for future in finished:
                key = pending.pop(future)
                try:
                    record = future.result()
                    with lock:
                        result["images"].append(record)
                except MigrationPaused as error:
                    with lock:
                        result["pause_reason"] = str(error)
                    stopped = True
                except (OSError, ValueError, RuntimeError) as error:
                    with lock:
                        result["errors"].append(
                            {"object_key": key, "error": str(error)}
                        )
                    stopped |= "download_cap_exceeded" in str(error)
                if (len(result["images"]) + len(result["errors"])) % 25 == 0:
                    checkpoint()
                    print(
                        f"Verified {len(result['images'])}/{expected_count} legacy images; "
                        f"failed {len(result['errors'])}",
                        flush=True,
                    )
            if not stopped:
                for _ in finished:
                    submit_next()
    result["images"].sort(key=lambda image: image["object_key"])
    result["unattempted_objects"] = (
        expected_count - len(result["images"]) - len(result["errors"])
    )
    cap_pause = (
        daily
        and result["errors"]
        and all("download_cap_exceeded" in error["error"] for error in result["errors"])
    )
    if cap_pause:
        result["pause_reason"] = "B2 account cap reached"
    result["status"] = (
        "failed"
        if result["errors"] and not cap_pause
        else "verified"
        if len(result["images"]) == expected_count
        else "partial"
    )
    checkpoint()
    if result["status"] == "failed":
        raise TestFailure(
            f"{len(result['errors'])} legacy image uploads failed: "
            + result["errors"][0]["error"]
        )
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
    protected = {path for reader in result["readers"] for path in reader["images"]}
    result["protected_paths"] = sorted(protected)
    result["protected_bytes"] = sum(images[path]["bytes"] for path in protected)
    write_json(output, result)
    return result


def publication_files(
    repo: Path,
    manifest: Path,
    receipt: Path,
    protected_paths: set[str],
) -> dict[Path, str]:
    inventory = read_inventory(manifest)
    images = {image["original_path"]: image for image in inventory["images"]}
    expected = {
        image["object_key"]: {
            key: image[key]
            for key in ("object_key", "sha256", "bytes", "content_type", "url")
        }
        for image in images.values()
    }
    verified = json.loads(receipt.read_text())
    actual = {
        image["object_key"]: {key: image[key] for key in expected[image["object_key"]]}
        for image in verified.get("images", [])
    }
    if (
        verified.get("status") != "verified"
        or verified.get("manifest_sha256") != digest(manifest.read_bytes())
        or actual != expected
        or not protected_paths <= images.keys()
    ):
        raise TestFailure("Complete matching upload verification is required")
    for image in images.values():
        source_bytes(repo, image)
    files = {}
    for path in sorted(repo.rglob("*.html")):
        relative = path.relative_to(repo)
        if any(part.startswith(".") for part in relative.parts):
            continue
        document = path.read_text()
        rewritten, used = rewrite_document(
            document, urljoin(PAGES_BASE, relative.as_posix()), images
        )
        if not used:
            continue
        if rewritten != document:
            files[relative] = rewritten
        metadata_path = path.with_name(path.name + ".images.json")
        metadata = (
            json.loads(metadata_path.read_text())
            if metadata_path.exists()
            else {"schema_version": 1, "images": []}
        )
        merged = {image["original_path"]: image for image in metadata["images"]}
        for original_path in used:
            image = images[original_path]
            merged[original_path] = image | {"repository_path": original_path}
        metadata["images"] = [merged[key] for key in sorted(merged)]
        files[metadata_path.relative_to(repo)] = (
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
        )
    excluded = sorted(images.keys() - protected_paths)
    if any(re.search(r"[*?\[\]\r\n]", path) for path in excluded):
        raise TestFailure("Unsupported pattern in a Pages image path")
    files[Path(".github/pages-excluded-assets.txt")] = "".join(
        f"/{path}\n" for path in excluded
    )
    return files


def retain_inventory(
    repo: Path, manifest: Path, revision: str, *, directory: Path | None = None
) -> int:
    from image_originals import store_original

    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise TestFailure("An immutable repository revision is required")
    inventory = read_inventory(manifest)
    unique = {image["object_key"]: image for image in inventory["images"]}
    for index, image in enumerate(unique.values(), start=1):
        store_original(
            image["url"],
            source_bytes(repo, image),
            image["content_type"],
            expected_sha256=image["sha256"],
            expected_bytes=image["bytes"],
            directory=directory,
            source_url=(
                f"https://raw.githubusercontent.com/beila/my-collection/{revision}/"
                + quote(image["original_path"], safe="/")
            ),
        )
        if index % 250 == 0:
            print(f"Retained {index}/{len(unique)} image originals", flush=True)
    return len(unique)


def reader_compatibility(before: str, after: str, images: dict[str, dict]) -> list[str]:
    from bs4 import BeautifulSoup

    def normalized(text):
        return "".join(unicodedata.normalize("NFC", text).split())

    source = BeautifulSoup(before, "html.parser")
    target = BeautifulSoup(after, "html.parser")
    for node in target.select("script, style, head"):
        node.decompose()
    target_text = normalized(target.get_text(" ", strip=True))
    missing = [
        node
        for node in source.select(
            "p, li, h1, h2, h3, h4, h5, h6, td, th, figcaption, pre"
        )
        if (text := normalized(node.get_text(" ", strip=True)))
        and text not in target_text
    ]
    rewritten, used = rewrite_document(before, PAGES_BASE, images)
    missing_images = [
        path for path in used if images[path]["url"] not in html.unescape(after)
    ]
    image_urls = {images[path]["url"] for path in used}

    def placements(document):
        result = Counter()
        for node in BeautifulSoup(document, "html.parser").select(
            "img, source, video, a"
        ):
            urls = {
                node.get(attribute, "")
                for attribute in ("src", "href", "poster", "data-src", "data-original")
            }
            urls.update(
                entry.strip().split()[0]
                for entry in node.get("srcset", "").split(",")
                if entry.strip()
            )
            for url in urls & image_urls:
                result[node.name, url] += 1
        return result

    missing_placements = placements(rewritten) - placements(after)
    errors = []
    if missing:
        errors.append(f"missing saved text blocks: {len(missing)}")
    if missing_images:
        errors.append(f"missing migrated image references: {len(missing_images)}")
    if missing_placements:
        errors.append(f"missing image placements: {sum(missing_placements.values())}")
    return errors


def refresh_readers(
    repo: Path,
    manifest: Path,
    capture: Path,
    output: Path,
    *,
    limit: int = 0,
    workers: int = 4,
    client_factory=None,
    fetch=None,
) -> dict:
    if not 1 <= workers <= 4 or limit < 0:
        raise TestFailure("Invalid Reader migration limits")
    if client_factory is None:
        from instapaper_v2 import InstapaperV2Client, access_token

        def client_factory():
            return InstapaperV2Client(access_token())

    if fetch is None:
        from discussion_publication import fetch_published_document

        fetch = fetch_published_document
    inventory = read_inventory(manifest)
    images = {image["original_path"]: image for image in inventory["images"]}
    readers = json.loads(capture.read_text())["readers"]
    previous = json.loads(output.read_text()) if output.exists() else {}
    if previous and previous.get("manifest_sha256") != digest(manifest.read_bytes()):
        raise TestFailure("Reader migration checkpoint changed inventory")
    results = previous.get("bookmarks", {})
    selected = [
        reader
        for reader in readers
        if reader["images"]
        and results.get(reader["bookmark_id"], {}).get("status") != "verified"
    ]
    if limit:
        selected = selected[:limit]
    result = {
        "schema_version": 1,
        "manifest_sha256": digest(manifest.read_bytes()),
        "bookmarks": results,
    }
    local = threading.local()
    write_json(output, result)

    def refresh(reader):
        identifier = reader["bookmark_id"]
        outcome = {"status": "pending", "images": reader["images"]}
        try:
            relative = image_path(reader["url"], PAGES_BASE)
            if not relative:
                raise TestFailure("Saved article has no collection path")
            source = (repo / relative).resolve()
            if not source.is_relative_to(repo.resolve()):
                raise TestFailure("Saved article escapes the collection")
            document = source.read_text()
            before = (capture.parent / "readers" / f"{identifier}.html").read_text()
            errors = reader_compatibility(before, document, images)
            if errors:
                raise TestFailure("; ".join(errors))
            if fetch(reader["url"]) != document.encode():
                raise TestFailure("Published article does not match the migration")
            if not hasattr(local, "client"):
                local.client = client_factory()
            client = local.client
            after = client.parse_bookmark(identifier, force=True)
            errors = reader_compatibility(before, after, images)
            for delay in (1, 3, 5):
                if not errors:
                    break
                time.sleep(delay)
                after = client.parse_bookmark(identifier, force=False)
                errors = reader_compatibility(before, after, images)
            if errors:
                raise TestFailure("; ".join(errors))
            destination = output.parent / "refreshed-readers" / f"{identifier}.html"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(after)
            destination.chmod(0o600)
            outcome = {"status": "verified", "sha256": digest(after.encode())}
        except (OSError, ValueError, RuntimeError) as error:
            outcome["error"] = str(error)
        return identifier, outcome

    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = [executor.submit(refresh, reader) for reader in selected]
        for index, future in enumerate(as_completed(pending), start=1):
            identifier, outcome = future.result()
            results[identifier] = outcome
            write_json(output, result)
            if index % 25 == 0:
                print(
                    f"Checked {index}/{len(selected)} saved reader updates", flush=True
                )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=("upload", "plan", "readers", "retain", "refresh")
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sha256")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bookmarks", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--revision")
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--resume-receipt", type=Path)
    parser.add_argument("--daily", action="store_true")
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
            resume_receipt=args.resume_receipt,
            daily=args.daily,
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
    elif args.operation == "readers":
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
    elif args.operation == "retain":
        if not args.revision:
            parser.error("retain requires --revision")
        count = retain_inventory(args.repo, args.manifest, args.revision)
        write_json(args.output, {"retained": count, "revision": args.revision})
        print(json.dumps({"retained": count}))
    else:
        if args.capture is None:
            parser.error("refresh requires --capture")
        result = refresh_readers(
            args.repo,
            args.manifest,
            args.capture,
            args.output,
            limit=args.limit,
            workers=min(args.workers, 4),
        )
        print(
            json.dumps(
                {
                    "verified": sum(
                        record["status"] == "verified"
                        for record in result["bookmarks"].values()
                    ),
                    "pending": sum(
                        record["status"] != "verified"
                        for record in result["bookmarks"].values()
                    ),
                }
            )
        )


if __name__ == "__main__":
    main()
