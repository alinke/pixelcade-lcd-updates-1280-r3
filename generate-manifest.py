#!/usr/bin/env python3
"""
Manifest generator for pixelcade-lcd-updates-r3 incremental artwork updates.

This script scans the repo for artwork files and maintains a manifest.json that tracks
when each file was added. Used by runupdate.sh to enable incremental downloads.

Usage:
    python3 generate-manifest.py          # Auto-run, bumps version only if new files found
    python3 generate-manifest.py --force  # Force version bump even if no new files
"""

import json
import os
import sys
from pathlib import Path

# Configuration
REPO_ROOT = Path(__file__).parent
MANIFEST_PATH = REPO_ROOT / "manifest.json"
BASE_VERSION = 19  # R3 starts at version 19

# Directories to scan for artwork
ARTWORK_DIRS = ["lcdmarquees", "metadata"]

# File extensions to include
ARTWORK_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".json", ".mp4"}


def get_all_artwork_files():
    """Scan repo and return set of all artwork file paths (relative to repo root)."""
    files = set()
    for dir_name in ARTWORK_DIRS:
        dir_path = REPO_ROOT / dir_name
        if not dir_path.exists():
            continue
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ARTWORK_EXTENSIONS:
                # Store relative path with forward slashes
                rel_path = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")
                files.add(rel_path)
    return files


def load_manifest():
    """Load existing manifest or return default structure."""
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load manifest, starting fresh: {e}")

    return {
        "version": BASE_VERSION,
        "base_version": BASE_VERSION,
        "files": []
    }


def save_manifest(manifest):
    """Save manifest to disk."""
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=False)
        f.write("\n")  # Trailing newline


def update_manifest(force_bump=False):
    """
    Update the manifest with any new files.

    Returns:
        tuple: (new_file_count, removed_file_count, new_version)
    """
    manifest = load_manifest()
    current_version = manifest.get("version", BASE_VERSION)

    # Build lookup of existing files
    existing_files = {f["path"]: f["added"] for f in manifest.get("files", [])}

    # Get current files in repo
    current_files = get_all_artwork_files()

    # Find new and removed files
    existing_paths = set(existing_files.keys())
    new_files = current_files - existing_paths
    removed_files = existing_paths - current_files

    # Determine if we need to bump version
    should_bump = force_bump or len(new_files) > 0
    new_version = current_version + 1 if should_bump else current_version

    # Build updated file list
    updated_files = []

    # Keep existing files (that still exist)
    for path in sorted(current_files):
        if path in existing_files:
            # File already tracked, keep its original version
            updated_files.append({"path": path, "added": existing_files[path]})
        else:
            # New file, tag with new version
            updated_files.append({"path": path, "added": new_version})

    # Update manifest
    manifest["version"] = new_version
    manifest["base_version"] = BASE_VERSION
    manifest["files"] = updated_files

    save_manifest(manifest)

    return len(new_files), len(removed_files), new_version


def main():
    force_bump = "--force" in sys.argv

    print(f"Scanning artwork directories: {ARTWORK_DIRS}")

    new_count, removed_count, version = update_manifest(force_bump)

    if new_count > 0:
        print(f"Added {new_count} new file(s) at version {version}")
    if removed_count > 0:
        print(f"Removed {removed_count} deleted file(s) from manifest")
    if new_count == 0 and removed_count == 0:
        if force_bump:
            print(f"No changes, but forced version bump to {version}")
        else:
            print(f"No changes detected. Manifest at version {version}")

    # Return non-zero if manifest was updated (for git hook to know to stage it)
    return 0 if (new_count == 0 and removed_count == 0 and not force_bump) else 1


if __name__ == "__main__":
    sys.exit(main())
