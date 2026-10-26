"""Retrieve only from Kaggle's official accessible route; never bypass login/access."""

import argparse
import hashlib
import json
import shutil
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

URL = "https://www.kaggle.com/api/v1/datasets/download/mlg-ulb/creditcardfraud"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("data/private"))
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    target = args.directory / "creditcard.csv"
    if target.exists():
        raise SystemExit("Dataset already exists; refusing to overwrite it.")
    archive = args.directory / "creditcard.zip.part"
    try:
        request = urllib.request.Request(URL, headers={"User-Agent": "ARGUS-research/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as out:
            if "zip" not in response.headers.get("Content-Type", ""):
                raise SystemExit(
                    "Official route did not return a ZIP. Use authorized Kaggle login/download manually."
                )
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    raise SystemExit("Unexpected archive size; stopped download")
                out.write(chunk)
        with zipfile.ZipFile(archive) as bundle:
            members = [m for m in bundle.infolist() if m.filename == "creditcard.csv"]
            if len(members) != 1 or members[0].file_size > 200 * 1024 * 1024:
                raise SystemExit("Unexpected dataset archive contents")
            # Write a fixed local destination instead of extracting user-controlled paths.
            with bundle.open(members[0]) as source, target.open("xb") as out:
                shutil.copyfileobj(source, out)
        with target.open("rb") as source:
            checksum = hashlib.file_digest(source, "sha256").hexdigest()
        metadata = {
            "source": URL,
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "csv_bytes": target.stat().st_size,
            "csv_sha256": checksum,
            "redistributed": False,
        }
        (args.directory / "source.json").write_text(json.dumps(metadata, indent=2))
        print(json.dumps(metadata))
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"Official Kaggle download returned HTTP {exc.code}. Complete authorized manual download; no alternate mirrors used."
        ) from exc
    finally:
        archive.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
