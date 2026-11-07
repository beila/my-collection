"""Exercise B2 image delivery without changing production image storage."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

BUCKET = "my-collection-images"
PREFIX = "image-hosting-test/v1/"
MAX_BYTES = 32 * 1024 * 1024
CONTENT_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}


class TestFailure(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def object_key(name: str, sha256: str) -> str:
    return f"{PREFIX}{sha256}/{name}"


def pack(output: Path, paths: list[Path]) -> None:
    images = []
    if not 1 <= len(paths) <= 12:
        raise TestFailure("Use between one and twelve test images")
    if len({path.name for path in paths}) != len(paths):
        raise TestFailure("Test image names must be unique")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            content = path.read_bytes()
            content_type = CONTENT_TYPES.get(path.suffix.lower())
            if content_type is None or not content or len(content) > MAX_BYTES:
                raise TestFailure("Unsupported image type or size")
            sha256 = digest(content)
            name = f"images/{path.name}"
            archive.writestr(name, content)
            images.append(
                {
                    "path": name,
                    "sha256": sha256,
                    "bytes": len(content),
                    "content_type": content_type,
                    "object_key": object_key(path.name, sha256),
                }
            )
        archive.writestr(
            "manifest.json", json.dumps({"schema_version": 1, "images": images})
        )
    print(
        json.dumps({"batch_sha256": digest(output.read_bytes()), "images": len(images)})
    )


def load_batch(path: Path, expected_hash: str) -> list[tuple[dict[str, Any], bytes]]:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise TestFailure("Invalid batch checksum")
    if path.stat().st_size > MAX_BYTES or digest(path.read_bytes()) != expected_hash:
        raise TestFailure("Batch checksum or size mismatch")
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 13 or sum(item.file_size for item in entries) > MAX_BYTES:
            raise TestFailure("Batch exceeds test limits")
        names = [entry.filename for entry in entries]
        if len(set(names)) != len(names):
            raise TestFailure("Duplicate archive entries")
        manifest = json.loads(archive.read("manifest.json"))
        images = manifest.get("images", [])
        if manifest.get("schema_version") != 1 or not 1 <= len(images) <= 12:
            raise TestFailure("Invalid image manifest")
        result = []
        for image in images:
            name = image["path"]
            relative = PurePosixPath(name)
            if (
                len(relative.parts) != 2
                or relative.parts[0] != "images"
                or relative.name in {".", ".."}
                or "\\" in name
                or name != relative.as_posix()
            ):
                raise TestFailure("Unsafe image path")
            content = archive.read(name)
            sha256 = digest(content)
            if (
                not content
                or image["bytes"] != len(content)
                or image["sha256"] != sha256
                or image["content_type"] != CONTENT_TYPES.get(relative.suffix.lower())
                or image["object_key"] != object_key(relative.name, sha256)
            ):
                raise TestFailure("Image manifest does not match its bytes")
            result.append((image, content))
        if set(names) != {"manifest.json", *(image["path"] for image, _ in result)}:
            raise TestFailure("Unexpected archive content")
        return result


def b2_endpoint(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
        or not any(
            host.endswith(f".{domain}")
            for domain in ("backblaze.com", "backblazeb2.com")
        )
    ):
        raise TestFailure("Unexpected B2 endpoint")
    return url.rstrip("/")


class B2:
    def __init__(self) -> None:
        self.opener = urllib.request.build_opener(NoRedirect())
        try:
            credentials = f"{os.environ['B2_APPLICATION_KEY_ID']}:{os.environ['B2_APPLICATION_KEY']}"
        except KeyError as error:
            raise TestFailure("B2 application secrets are missing") from error
        authorization = "Basic " + base64.b64encode(credentials.encode()).decode()
        account = self.request_json(
            "https://api.backblazeb2.com/b2api/v4/b2_authorize_account",
            authorization,
        )
        storage = account["apiInfo"]["storageApi"]
        allowed = storage["allowed"]
        buckets = allowed["buckets"]
        if (
            not isinstance(buckets, list)
            or len(buckets) != 1
            or buckets[0].get("name") not in {BUCKET, None}
            or not {"readFiles", "writeFiles"} <= set(allowed["capabilities"])
        ):
            raise TestFailure(
                "Use a read/write application key restricted to the test bucket"
            )
        self.bucket_id = buckets[0]["id"]
        self.name_prefix = allowed.get("namePrefix") or ""
        self.api_url = b2_endpoint(storage["apiUrl"])
        self.download_url = b2_endpoint(storage["downloadUrl"])
        self.authorization = account["authorizationToken"]

    def request_json(
        self, url: str, authorization: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            b2_endpoint(url),
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Authorization": authorization,
                "Content-Type": "application/json",
            },
        )
        try:
            with self.opener.open(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise TestFailure(f"B2 API request failed with HTTP {error.code}") from None

    def public_url(self, image: dict[str, Any]) -> str:
        return f"{self.download_url}/file/{BUCKET}/" + urllib.parse.quote(
            image["object_key"], safe="/"
        )

    def verify(self, image: dict[str, Any]) -> bool:
        try:
            with self.opener.open(self.public_url(image), timeout=60) as response:
                content = response.read(MAX_BYTES + 1)
                content_type = response.headers.get_content_type()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return False
            raise TestFailure(
                f"Anonymous image read failed with HTTP {error.code}"
            ) from None
        if (
            digest(content) != image["sha256"]
            or len(content) != image["bytes"]
            or content_type != image["content_type"]
        ):
            raise TestFailure("Public image checksum, size, or content type mismatch")
        return True

    def upload(self, image: dict[str, Any], content: bytes) -> None:
        if not image["object_key"].startswith(self.name_prefix):
            raise TestFailure(
                "Object key is outside the application's permitted prefix"
            )
        target = self.request_json(
            f"{self.api_url}/b2api/v4/b2_get_upload_url",
            self.authorization,
            {"bucketId": self.bucket_id},
        )
        request = urllib.request.Request(
            b2_endpoint(target["uploadUrl"]),
            data=content,
            method="POST",
            headers={
                "Authorization": target["authorizationToken"],
                "X-Bz-File-Name": urllib.parse.quote(image["object_key"], safe="/"),
                "Content-Type": image["content_type"],
                "Content-Length": str(len(content)),
                "X-Bz-Content-Sha1": hashlib.sha1(content).hexdigest(),
                "X-Bz-Info-b2-cache-control": urllib.parse.quote(
                    "public, max-age=31536000, immutable", safe=""
                ),
            },
        )
        try:
            with self.opener.open(request, timeout=120) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            raise TestFailure(f"Image upload failed with HTTP {error.code}") from None
        if result.get("fileName") != image["object_key"]:
            raise TestFailure("Uploaded object key mismatch")


def document(images: list[dict[str, Any]]) -> str:
    figures = []
    for index, image in enumerate(images, 1):
        url = html.escape(image["url"], quote=True)
        caption = html.escape(PurePosixPath(image["path"]).name)
        figures.append(
            f'<figure><a href="{url}"><img src="{url}" srcset="{url} 1x" '
            f'alt="Synthetic image {index}"></a><figcaption>{caption}</figcaption></figure>'
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Collection image hosting test</title>"
        "<style>body{max-width:46rem;margin:3rem auto;padding:0 1rem;"
        "font:18px/1.6 system-ui}img{max-width:100%;height:auto}figure{margin:2rem 0}</style>"
        "</head><body><article><h1>Collection image hosting test</h1>"
        "<p>This separate test page checks synthetic images served from Backblaze B2. "
        "The images were uploaded through GitHub Actions and verified before publication.</p>"
        + "".join(figures)
        + "<p>End of the image hosting test.</p></article></body></html>\n"
    )


def upload_batch(
    batch: list[tuple[dict[str, Any], bytes]], output: Path, *, interrupt_after: int = 0
) -> dict[str, Any]:
    if output.exists():
        raise TestFailure("Use a fresh output directory for each attempt")
    client = B2()
    images = []
    uploaded = 0
    reused = 0
    for index, (image, content) in enumerate(batch, 1):
        if client.verify(image):
            reused += 1
        else:
            client.upload(image, content)
            uploaded += 1
            if not client.verify(image):
                raise TestFailure("Uploaded image is not anonymously reachable")
        images.append({**image, "url": client.public_url(image)})
        print(f"Verified image {index}/{len(batch)}", flush=True)
        if interrupt_after and index == interrupt_after:
            raise TestFailure("Intentional interruption: no page was produced")
    result = {
        "schema_version": 1,
        "images": images,
        "uploaded": uploaded,
        "reused": reused,
    }
    output.mkdir(parents=True)
    (output / "index.html").write_text(document(images), encoding="utf-8")
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"uploaded": uploaded, "reused": reused}))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    packing = commands.add_parser("pack")
    packing.add_argument("--output", type=Path, required=True)
    packing.add_argument("images", type=Path, nargs="+")
    uploading = commands.add_parser("upload")
    uploading.add_argument("--batch", type=Path, required=True)
    uploading.add_argument("--sha256", required=True)
    uploading.add_argument("--output", type=Path, required=True)
    uploading.add_argument("--interrupt-after", type=int, default=0)
    args = parser.parse_args()
    try:
        if args.command == "pack":
            pack(args.output, args.images)
        else:
            upload_batch(
                load_batch(args.batch, args.sha256),
                args.output,
                interrupt_after=args.interrupt_after,
            )
    except (TestFailure, urllib.error.URLError) as error:
        message = (
            str(error) if isinstance(error, TestFailure) else "Network request failed"
        )
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
