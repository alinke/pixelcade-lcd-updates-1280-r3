#!/usr/bin/env python3
"""
Manifest generator for pixelcade-lcd-updates-1280-r3 incremental artwork updates.

This script scans the repo for artwork files and maintains a manifest.json that tracks
when each file was added. Used by runupdate.sh to enable incremental downloads.

Usage:
    python3 generate-manifest.py              # Auto-run, bumps version only if new files found
    python3 generate-manifest.py --force      # Force version bump even if no new files
    python3 generate-manifest.py --reset 25   # Reset manifest with new base version (after moving files to R2)
"""

import json
import os
import sys
import argparse
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


def reset_manifest(new_base_version):
    """
    Reset the manifest with a new base version.
    All existing files are tagged with the new base version.
    Use this after moving files from R3 to R2.

    Returns:
        tuple: (file_count, new_version)
    """
    current_files = get_all_artwork_files()

    # Build fresh manifest with all files at new base version
    updated_files = []
    for path in sorted(current_files):
        updated_files.append({"path": path, "added": new_base_version})

    manifest = {
        "version": new_base_version,
        "base_version": new_base_version,
        "files": updated_files
    }

    save_manifest(manifest)

    return len(current_files), new_base_version


def main():
    parser = argparse.ArgumentParser(
        description="Generate manifest for incremental artwork updates"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force version bump even if no new files"
    )
    parser.add_argument(
        "--reset",
        type=int,
        metavar="VERSION",
        help="Reset manifest with new base version (use after moving files to R2)"
    )
    args = parser.parse_args()

    print(f"Scanning artwork directories: {ARTWORK_DIRS}")

    if args.reset is not None:
        # Reset mode - fresh start with new base version
        file_count, version = reset_manifest(args.reset)
        print(f"Reset manifest to version {version} with {file_count} files")
        print(f"All files tagged with base version {version}")
        return 1  # Always indicate manifest was updated

    # Normal mode - incremental update
    new_count, removed_count, version = update_manifest(args.force)

    if new_count > 0:
        print(f"Added {new_count} new file(s) at version {version}")
    if removed_count > 0:
        print(f"Removed {removed_count} deleted file(s) from manifest")
    if new_count == 0 and removed_count == 0:
        if args.force:
            print(f"No changes, but forced version bump to {version}")
        else:
            print(f"No changes detected. Manifest at version {version}")

    # Return non-zero if manifest was updated (for git hook to know to stage it)
    return 0 if (new_count == 0 and removed_count == 0 and not args.force) else 1


if __name__ == "__main__":
    sys.exit(main())
