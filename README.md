# Pixelcade LCD Artwork Updates - R3 (1280x390)

This repository contains incremental artwork updates for Pixelcade LCD displays at 1280x390 resolution.

## Repository Structure

- `lcdmarquees/` - Marquee images organized by system
- `metadata/` - Metadata JSON files
- `manifest.json` - Tracks all files and when they were added (for incremental updates)
- `generate-manifest.py` - Script to update the manifest

## How Incremental Updates Work

The manifest system allows users to download only new files instead of the entire repository:

1. Each file in `manifest.json` has an `added` version number
2. User's device stores its current artwork version in `ARTWORKVERSION`
3. During update, only files where `added > currentVersion` are downloaded
4. If more than 100 new files are needed, falls back to full zip download

## For Developers

### Setup (One Time)

Configure git to use the pre-commit hook:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

### Normal Workflow

Just commit your artwork changes normally. The pre-commit hook automatically:
1. Detects new files in `lcdmarquees/` or `metadata/`
2. Updates `manifest.json` with new files tagged at the next version
3. Stages the updated manifest

```bash
# Add your new artwork
cp new-marquee.png lcdmarquees/arcade/

# Commit - manifest is auto-updated
git add .
git commit -m "Added new-marquee"
git push
```

### Manual Manifest Update

If needed, you can manually run the manifest generator:

```bash
# Normal update (only bumps version if new files found)
python3 generate-manifest.py

# Force version bump even with no changes
python3 generate-manifest.py --force

# Reset manifest after major reorganization (see below)
python3 generate-manifest.py --reset 25
```

## Moving Files to R2 (Major Reorganization)

When R3 gets too large, you can move established files to R2 (the base layer) and reset R3 to only track new additions.

### Process

1. **Copy files from R3 to R2:**
   ```bash
   # Copy the files you want to move
   cp -r lcdmarquees/arcade/* ../pixelcade-lcd-updates/lcdmarquees/arcade/
   ```

2. **Commit R2 changes:**
   ```bash
   cd ../pixelcade-lcd-updates
   git add .
   git commit -m "Added artwork from R3"
   git push
   ```

3. **Remove moved files from R3:**
   ```bash
   cd ../pixelcade-lcd-updates-1280-r3
   rm lcdmarquees/arcade/moved-file1.png
   rm lcdmarquees/arcade/moved-file2.png
   # etc.
   ```

4. **Reset R3 manifest with new base version:**
   ```bash
   # Choose a version number higher than current (check manifest.json for current)
   python3 generate-manifest.py --reset 25
   ```

5. **Update ARTWORKVERSION in update-lcd.json:**
   Update the `latestArtworkVersion` in the main update config to match the new base version.

6. **Commit R3 changes:**
   ```bash
   git add .
   git commit -m "Reset manifest after moving files to R2"
   git push
   ```

### What --reset Does

- Scans all remaining files in the repo
- Creates a fresh manifest with all files tagged at the new base version
- Sets both `version` and `base_version` to the new value
- Effectively creates a new baseline for incremental updates

## Version Numbering

- R1 (base): versions 1-10
- R2: versions 11-18
- R3: versions 19+ (starts at `base_version: 19`)

After a reset, the base version moves up (e.g., to 25), and incremental tracking starts fresh from there.

## Manifest Format

```json
{
  "version": 25,
  "base_version": 19,
  "files": [
    {"path": "lcdmarquees/arcade/pacman.png", "added": 19},
    {"path": "lcdmarquees/arcade/galaga.png", "added": 22},
    {"path": "lcdmarquees/arcade/newgame.png", "added": 25}
  ]
}
```

- `version`: Current manifest version (increments when new files added)
- `base_version`: Minimum version this repo supports (files before this are in R1/R2)
- `files[].path`: Relative path to file
- `files[].added`: Version when file was added to manifest
