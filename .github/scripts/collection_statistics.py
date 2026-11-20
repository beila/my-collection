"""Measure the staged website and project migration receipts into public totals."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from legacy_image_migration import (
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
IMAGE_STORAGE_FIELDS = (
    "github_deployed_bytes",
    "github_new_bytes",
    "backblaze_legacy_bytes",
    "backblaze_new_bytes",
)


def size_observation(report: dict) -> dict:
    measured_at = datetime.fromisoformat(report["measured_at"])
    if measured_at.tzinfo is None:
        raise ValueError("Deployment measurement has no timezone")
    site = report["site"]
    categories = {}
    for name in ("images", "html", "other"):
        row = site["categories"][name]
        if any(
            type(row.get(key)) is not int or row[key] < 0 for key in ("files", "bytes")
        ):
            raise ValueError("Invalid deployment measurement")
        categories[name] = {key: row[key] for key in ("files", "bytes")}
    if any(
        type(site.get(key)) is not int
        or site[key] != sum(row[key] for row in categories.values())
        for key in ("files", "bytes")
    ):
        raise ValueError("Deployment totals do not match their categories")
    deployment = report.get("deployment", {})
    run_id = str(deployment.get("GITHUB_RUN_ID", ""))
    attempt = str(deployment.get("GITHUB_RUN_ATTEMPT", "1"))
    if not run_id.isdecimal() or not attempt.isdecimal():
        raise ValueError("Deployment measurement has no run identity")
    observation = {
        "measured_at": measured_at.astimezone(UTC).isoformat(),
        "deployment": {"GITHUB_RUN_ID": run_id, "GITHUB_RUN_ATTEMPT": attempt},
        "site": {
            **{key: site[key] for key in ("files", "bytes")},
            "categories": categories,
        },
    }
    migration = report.get("migration", {})
    if migration and migration.get("available", True):
        fields = (
            "objects",
            "verified_objects",
            "bytes",
            "verified_bytes",
            "legacy_files",
            "remaining_files",
            "remaining_bytes",
            "errors",
        )
        if any(
            type(migration.get(key)) is not int or migration[key] < 0 for key in fields
        ):
            raise ValueError("Invalid migration observation")
        observation["migration"] = {key: migration[key] for key in fields}
        observation["migration"]["checkpoint"] = (
            "latest" if migration.get("checkpoint") == "latest" else "baseline"
        )
    originals = report.get("repository_originals", {})
    if all(
        type(originals.get(key)) is int and originals[key] >= 0
        for key in ("files", "bytes")
    ):
        observation["repository_originals"] = {
            key: originals[key] for key in ("files", "bytes")
        }
    storage = report.get("image_storage")
    if storage is None:
        storage = {
            "github_deployed_bytes": categories["images"]["bytes"],
            "github_new_bytes": None,
            "backblaze_legacy_bytes": (
                migration.get("verified_bytes")
                if migration.get("checkpoint") == "latest"
                else None
            ),
            "backblaze_new_bytes": None,
        }
    if not isinstance(storage, dict) or any(
        value is not None and (type(value) is not int or value < 0)
        for value in (storage.get(key) for key in IMAGE_STORAGE_FIELDS)
    ):
        raise ValueError("Invalid image storage measurement")
    observation["image_storage"] = {
        key: storage.get(key) for key in IMAGE_STORAGE_FIELDS
    }
    return observation


def read_history(paths: list[Path], now: str) -> list[dict]:
    latest = datetime.fromisoformat(now)
    observations = {}
    for path in paths:
        document = json.loads(path.read_text())
        rows = document.get("history", [document])
        if not isinstance(rows, list):
            raise ValueError("Invalid deployment history")
        if "site" in document and document.get("deployment", {}).get("GITHUB_RUN_ID"):
            rows = [*rows, document]
        for row in rows:
            item = size_observation(row)
            if datetime.fromisoformat(item["measured_at"]) <= latest:
                observations[item["deployment"]["GITHUB_RUN_ID"]] = item
    return sorted(observations.values(), key=lambda row: row["measured_at"])


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


def migration_checkpoint(repo: Path, checkpoint_dir: Path | None) -> tuple:
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
    return inventory, expected, verified, metadata, seen


def migration_totals(repo: Path, site: Path, checkpoint_dir: Path | None) -> dict:
    inventory, expected, verified, metadata, seen = migration_checkpoint(
        repo, checkpoint_dir
    )
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
        "limits": {"read_requests": DAILY_READ_REQUESTS},
    }


def image_storage_totals(repo: Path, checkpoint_dir: Path | None) -> dict:
    result = dict.fromkeys(IMAGE_STORAGE_FIELDS)
    archived = {}
    root = repo / "image-originals/images/v1"
    try:
        inventory = read_inventory(repo / ".github/legacy-image-migration.json")
        expected = {row["object_key"]: row for row in inventory["images"]}
        if root.is_dir():
            for path in root.iterdir():
                if (
                    path.is_symlink()
                    or not path.is_file()
                    or path.suffix.lower() not in IMAGE_EXTENSIONS
                    or not re.fullmatch(r"[0-9a-f]{64}", path.stem)
                ):
                    raise ValueError("Invalid archived image identity")
                content = path.read_bytes()
                if not content or hashlib.sha256(content).hexdigest() != path.stem:
                    raise ValueError("Archived image checksum mismatch")
                archived["images/v1/" + path.name] = len(content)
        if any(
            size != expected[key]["bytes"]
            for key, size in archived.items()
            if key in expected
        ):
            raise ValueError("Conflicting stored image size")
        new_bytes = sum(size for key, size in archived.items() if key not in expected)
        result["github_new_bytes"] = result["backblaze_new_bytes"] = new_bytes
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        return result
    try:
        _inventory, expected, _receipt, metadata, seen = migration_checkpoint(
            repo, checkpoint_dir
        )
        if metadata:
            legacy = seen | (archived.keys() & expected.keys())
            result["backblaze_legacy_bytes"] = sum(
                expected[key]["bytes"] for key in legacy
            )
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        pass
    return result


def write_report(
    repo: Path,
    site: Path,
    checkpoint_dir: Path | None = None,
    *,
    now: str | None = None,
    history_paths: list[Path] | None = None,
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
    history = read_history(history_paths or [], report["measured_at"])
    report["history"] = history
    report["history_days"] = None
    report["history_limit"] = None
    try:
        report["migration"] = migration_totals(repo, site, checkpoint_dir)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        report["migration"] = {"available": False}
    try:
        report["repository_originals"] = tree_totals(repo / "image-originals")
        report["image_storage"] = image_storage_totals(repo, checkpoint_dir)
        # Include this report in the staged file and byte counts.
        for _attempt in range(10):
            output.write_text(json.dumps(report, ensure_ascii=False) + "\n")
            measured = tree_totals(site)
            if report.get("site") == measured:
                return report
            report["site"] = measured
            report["image_storage"]["github_deployed_bytes"] = measured["categories"][
                "images"
            ]["bytes"]
            if report["deployment"].get("GITHUB_RUN_ID"):
                current = size_observation(report)
                prior = [
                    row
                    for row in history
                    if row["deployment"]["GITHUB_RUN_ID"]
                    != current["deployment"]["GITHUB_RUN_ID"]
                ]
                report["history"] = prior + [current]
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
    parser.add_argument("--history", type=Path, action="append", default=[])
    args = parser.parse_args()
    report = write_report(
        args.repo, args.site, args.checkpoint_dir, history_paths=args.history
    )
    print(json.dumps({"site": report["site"], "migration": report["migration"]}))


if __name__ == "__main__":
    main()
