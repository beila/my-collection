"""Validate and upload bounded converter image batches on GitHub Actions."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

from b2_image_hosting_test import B2, MAX_BYTES, TestFailure, digest

PREFIX = "images/v1/"
CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}
MAX_IMAGES = 12


def object_key(sha256: str, extension: str) -> str:
    return f"{PREFIX}{sha256}{extension}"


def load_batch(path: Path, expected_hash: str) -> list[tuple[dict, bytes]]:
    if (
        not re.fullmatch(r"[0-9a-f]{64}", expected_hash)
        or path.stat().st_size > MAX_BYTES
        or digest(path.read_bytes()) != expected_hash
    ):
        raise TestFailure("Image batch checksum or size mismatch")
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if (
            len(entries) > MAX_IMAGES + 1
            or len(set(names)) != len(names)
            or sum(entry.file_size for entry in entries) > MAX_BYTES
        ):
            raise TestFailure("Image batch exceeds limits or has duplicate entries")
        manifest = json.loads(archive.read("manifest.json"))
        images = manifest.get("images", [])
        if manifest.get("schema_version") != 1 or not 1 <= len(images) <= MAX_IMAGES:
            raise TestFailure("Invalid image batch manifest")
        result = []
        for image in images:
            extension = Path(image["path"]).suffix
            sha256 = image["sha256"]
            if (
                not isinstance(sha256, str)
                or not re.fullmatch(r"[0-9a-f]{64}", sha256)
                or extension not in CONTENT_TYPES
                or image["object_key"] != object_key(sha256, extension)
                or image["path"] != image["object_key"]
                or image["content_type"] != CONTENT_TYPES[extension]
            ):
                raise TestFailure("Invalid image object identity")
            content = archive.read(image["path"])
            if (
                not content
                or len(content) != image["bytes"]
                or digest(content) != sha256
            ):
                raise TestFailure("Image bytes do not match the manifest")
            result.append((image, content))
        if set(names) != {"manifest.json", *(image["path"] for image, _ in result)}:
            raise TestFailure("Unexpected image batch content")
        return result


def upload_batch(path: Path, expected_hash: str, output: Path) -> dict:
    batch = load_batch(path, expected_hash)
    client = B2()
    images = []
    uploaded = 0
    for image, content in batch:
        if not client.verify(image):
            client.upload(image, content)
            uploaded += 1
            if not client.verify(image):
                raise TestFailure("Uploaded image is not anonymously reachable")
        images.append({**image, "url": client.public_url(image)})
    result = {
        "schema_version": 1,
        "batch_sha256": expected_hash,
        "images": images,
        "uploaded": uploaded,
        "reused": len(images) - uploaded,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = upload_batch(args.batch, args.sha256, args.output)
    print(json.dumps({key: result[key] for key in ("uploaded", "reused")}))


if __name__ == "__main__":
    main()
