#!/usr/bin/env python3
"""
Downloads all IPL ball-by-ball data from Cricsheet.org — free, ~50MB.
Run once before build_models.py.

Usage: python scripts/download_cricsheet.py
"""
import sys, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from config.settings import CRICSHEET_URL, CRICSHEET_ZIP, DATA_RAW

def main():
    json_dir = DATA_RAW / "ipl_json"
    if json_dir.exists() and any(json_dir.glob("*.json")):
        count = len(list(json_dir.glob("*.json")))
        print(f"Already have {count} match files in {json_dir}")
        print("Delete data/raw/ipl_json/ to force re-download.")
        return

    print(f"Downloading IPL data from Cricsheet...")
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    resp = requests.get(CRICSHEET_URL, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(CRICSHEET_ZIP, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r  {pct:.1f}% ({downloaded//1024//1024}MB)", end="", flush=True)
    print(f"\nSaved to {CRICSHEET_ZIP}")

    print("Extracting...")
    json_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(CRICSHEET_ZIP, "r") as zf:
        members = [m for m in zf.namelist() if m.endswith(".json")]
        zf.extractall(json_dir, members=[m for m in zf.namelist()])
    count = len(list(json_dir.glob("*.json")))
    print(f"Extracted {count} match files to {json_dir}")
    print("\nNext step: python scripts/build_models.py")

if __name__ == "__main__":
    main()
