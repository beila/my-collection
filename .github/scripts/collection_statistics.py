"""Measure the staged website and project migration receipts into public totals."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from legacy_image_migration import (
    DAILY_DOWNLOAD_BYTES,
    DAILY_IMAGES,
    DAILY_READ_REQUESTS,
    read_inventory,
)

IMAGE_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
}


def tree_totals(root: Path) -> dict:
    totals = {name: {"files": 0, "bytes": 0} for name in ("images", "html", "other")}
    for directory, _folders, files in os.walk(root):
        for name in files:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError("A staged file is a symbolic link")
            suffix = path.suffix.lower()
            category = (
                "images"
                if suffix in IMAGE_EXTENSIONS
                else "html"
                if suffix in {".html", ".htm"}
                else "other"
            )
            totals[category]["files"] += 1
            totals[category]["bytes"] += path.stat().st_size
    return {
        "files": sum(row["files"] for row in totals.values()),
        "bytes": sum(row["bytes"] for row in totals.values()),
        "categories": totals,
    }


def migration_totals(repo: Path, site: Path, checkpoint_dir: Path | None) -> dict:
    manifest = repo / ".github/legacy-image-migration.json"
    inventory = read_inventory(manifest)
    expected = {row["object_key"]: row for row in inventory["images"]}
    receipt = repo / ".github/legacy-image-verified.json"
    metadata = {}
    if checkpoint_dir is not None:
        downloaded = checkpoint_dir / "legacy-image-receipt.json"
        meta_path = checkpoint_dir / "checkpoint.json"
        if downloaded.is_file() and meta_path.is_file():
            receipt = downloaded
            metadata = json.loads(meta_path.read_text())
            datetime.fromisoformat(metadata["updated_at"].replace("Z", "+00:00"))
    verified = json.loads(receipt.read_text())
    if verified.get("manifest_sha256") != hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest() or verified.get("status") not in {"partial", "verified", "failed"}:
        raise ValueError("Migration checkpoint does not match the inventory")
    seen = set()
    for row in verified["images"]:
        key = row["object_key"]
        if (
            key in seen
            or key not in expected
            or any(
                row.get(field) != expected[key][field]
                for field in ("sha256", "bytes", "content_type", "url")
            )
        ):
            raise ValueError("Migration checkpoint contains an invalid object")
        seen.add(key)
    if verified["status"] == "verified" and len(seen) != len(expected):
        raise ValueError("Verified migration checkpoint is incomplete")
    remaining = [
        site / row["original_path"]
        for row in inventory["images"]
        if (site / row["original_path"]).is_file()
    ]
    daily = verified.get("daily_upload", {})
    usage = {}
    if daily:
        datetime.strptime(daily["date"], "%Y-%m-%d")
        for key in ("read_requests", "download_bytes"):
            if type(daily.get(key)) is not int or daily[key] < 0:
                raise ValueError("Invalid daily migration usage")
        usage = {
            "date": daily["date"],
            "objects": len(set(daily["objects"])),
            "read_requests": daily["read_requests"],
            "download_bytes": daily["download_bytes"],
        }
    return {
        "available": True,
        "checkpoint": "latest" if metadata else "baseline",
        "updated_at": metadata.get("updated_at"),
        "status": verified["status"],
        "objects": len(expected),
        "verified_objects": len(seen),
        "bytes": sum(row["bytes"] for row in expected.values()),
        "verified_bytes": sum(expected[key]["bytes"] for key in seen),
        "legacy_files": len(inventory["images"]),
        "remaining_files": len(remaining),
        "remaining_bytes": sum(path.stat().st_size for path in remaining),
        "errors": len(verified.get("errors", [])),
        "daily": usage,
        "limits": {
            "objects": DAILY_IMAGES,
            "read_requests": DAILY_READ_REQUESTS,
            "download_bytes": DAILY_DOWNLOAD_BYTES,
        },
    }


def write_report(
    repo: Path,
    site: Path,
    checkpoint_dir: Path | None = None,
    *,
    now: str | None = None,
) -> dict:
    output = site / "sources/collection.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "measured_at": now or datetime.now(UTC).isoformat(),
        "deployment": {
            key: os.environ[key]
            for key in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA")
            if key in os.environ
        },
    }
    try:
        report["migration"] = migration_totals(repo, site, checkpoint_dir)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        report["migration"] = {"available": False}
    try:
        report["repository_originals"] = tree_totals(repo / "image-originals")
        # Include this report in the staged file and byte counts.
        for _attempt in range(10):
            output.write_text(json.dumps(report, ensure_ascii=False) + "\n")
            measured = tree_totals(site)
            if report.get("site") == measured:
                return report
            report["site"] = measured
        raise ValueError("Staged measurements did not converge")
    except (OSError, ValueError):
        report["site"] = {"available": False}
        output.write_text(json.dumps(report, ensure_ascii=False) + "\n")
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--checkpoint-dir", type=Path)
    args = parser.parse_args()
    report = write_report(args.repo, args.site, args.checkpoint_dir)
    print(json.dumps({"site": report["site"], "migration": report["migration"]}))


if __name__ == "__main__":
    main()
