"""Download the author-linked public PaySim dataset; no mirrors or access bypass."""

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

URL = "https://www.kaggle.com/api/v1/datasets/download/ealaxi/paysim1"
SOURCE = "https://www.kaggle.com/datasets/ealaxi/paysim1"


def download(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "paysim.csv"
    if target.exists():
        raise ValueError("PaySim CSV already exists; refusing to overwrite")
    # Temporary files are removed even on interruption; never extract archive paths.
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        archive = Path(temporary) / "download.zip"
        request = urllib.request.Request(URL, headers={"User-Agent": "ARGUS-research/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as out:
            if "zip" not in response.headers.get("Content-Type", ""):
                raise ValueError(
                    "Official route did not return a ZIP; use authorized manual access"
                )
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 250 * 1024 * 1024:
                    raise ValueError("Unexpected archive size")
                out.write(chunk)
        with zipfile.ZipFile(archive) as bundle:
            members = [m for m in bundle.infolist() if m.filename.endswith(".csv")]
            if len(members) != 1 or members[0].file_size > 600 * 1024 * 1024:
                raise ValueError("Unexpected archive contents or expanded size")
            staged = Path(temporary) / "paysim.csv"
            with bundle.open(members[0]) as source, staged.open("xb") as out:
                shutil.copyfileobj(source, out)
        with staged.open("rb") as source:
            checksum = hashlib.file_digest(source, "sha256").hexdigest()
        # Exclusive destination creation protects preexisting work.
        with staged.open("rb") as source, target.open("xb") as out:
            shutil.copyfileobj(source, out)
    metadata = {
        "dataset_id": "paysim",
        "data_kind": "synthetic",
        "source": SOURCE,
        "download_url": URL,
        "license": "CC BY-SA 4.0",
        "attribution": "E. A. Lopez-Rojas, A. Elmir, S. Axelsson; PaySim (EMSS 2016)",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "csv_bytes": target.stat().st_size,
        "csv_sha256": checksum,
        "redistributed": False,
    }
    (directory / "source.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("data/private/paysim"))
    args = parser.parse_args()
    try:
        print(json.dumps(download(args.directory), indent=2))
    except (urllib.error.URLError, ValueError) as exc:
        raise SystemExit(f"Official download failed: {exc}. No alternate source used.") from exc
