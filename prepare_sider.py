"""Prepare SIDER from official HTTPS links; the release version is not verified."""

import argparse
import csv
import gzip
import hashlib
import json
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

VERSION = "unverified_release"
SOURCE = "https://sideeffects.embl.de/download/"
FILES = {
    "drug_names.tsv": "https://sideeffects.embl.de/media/download/drug_names.tsv",
    "meddra_all_se.tsv.gz": "https://sideeffects.embl.de/media/download/meddra_all_se.tsv.gz",
}
MAX_DOWNLOAD = 256 * 1024 * 1024


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url, path):
    # Default TLS and certificate verification remain enabled.
    with urlopen(url, timeout=60) as response, path.open("xb") as handle:
        if not response.geturl().lower().startswith("https://"):
            raise ValueError("The download redirected away from HTTPS; stopping")
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD:
                raise ValueError("Download exceeds the size limit")
            handle.write(chunk)


def validate_files(folder):
    names = 0
    with (folder / "drug_names.tsv").open(encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) < 2 or not re.fullmatch(r"CID\d+", row[0]) or not row[1].strip():
                raise ValueError("Invalid drug_names.tsv row; expected a STITCH CID and a drug name")
            names += 1
    events = 0
    pt_rows = 0
    # Reading the complete gzip stream also checks its CRC/trailer.
    with gzip.open(folder / "meddra_all_se.tsv.gz", "rt", encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) < 6 or not re.fullmatch(r"CID\d+", row[0]) or not re.fullmatch(r"CID\d+", row[1]):
                raise ValueError("Invalid meddra_all_se.tsv.gz row; expected the official six-column format")
            events += 1
            if row[3] == "PT":
                if not row[5].strip():
                    raise ValueError("A MedDRA PT row has an empty event term")
                pt_rows += 1
    if not names or not events or not pt_rows:
        raise ValueError("Dataset is empty or contains no PT event records")
    return {"drug_name_rows": names, "side_effect_rows": events, "pt_rows": pt_rows}


def prepare(destination, source_directory=None, manual_source_url=None):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Output directory already exists. Keep the existing dataset or choose another --output-dir; nothing was overwritten.")
    if source_directory is not None and not manual_source_url:
        raise ValueError("Manual files require --source-url identifying their actual download source")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Validate in a temporary directory; never publish a partial dataset as ready.
    with tempfile.TemporaryDirectory(prefix=".sider_prepare_", dir=destination.parent) as temporary:
        staging = Path(temporary)
        provenance = {}
        for filename, url in FILES.items():
            target = staging / filename
            if source_directory is None:
                print(f"Downloading {url}", flush=True)
                download(url, target)
                provenance[filename] = {"download_url": url, "acquisition": "https_download"}
            else:
                original = Path(source_directory) / filename
                if not original.is_file():
                    raise ValueError(f"Missing manual source file: {original}")
                shutil.copyfile(original, target)
                provenance[filename] = {"source_url": manual_source_url,
                                        "acquisition": "user_provided_file; source not independently verified"}
        print("Validating both files and the full gzip stream...", flush=True)
        counts = validate_files(staging)
        for filename in FILES:
            provenance[filename].update(sha256=sha256(staging / filename), bytes=(staging / filename).stat().st_size)
        manifest = {
            "version": VERSION, "source_url": manual_source_url or SOURCE,
            "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
            "files": provenance, "validation": counts,
            "limitations": [
                "The download URLs are unversioned. The dataset release and compatibility of these two files have not been independently verified; do not describe them as SIDER 4.1.",
                "SIDER is an older label-derived dataset and may not contain the target drug.",
                "Format and gzip checks do not establish authenticity or completeness. Locally calculated SHA-256 hashes identify the saved files; they are not publisher checksums.",
                "Drug/event non-matches do not establish absence of risk.",
                "Review the official source documentation and data-use conditions before use.",
            ],
        }
        (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        # Allocate a new directory exclusively; preserve any pre-existing files.
        destination.mkdir(exist_ok=False)
        try:
            for path in staging.iterdir():
                shutil.move(str(path), str(destination / path.name))
        except Exception:
            # Only this newly allocated destination belongs to this operation.
            shutil.rmtree(destination)
            raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/sider_local"))
    parser.add_argument("--from-directory", type=Path, help="Directory with both manually obtained official SIDER files")
    parser.add_argument("--source-url", help="Actual download source for manually supplied files")
    args = parser.parse_args()
    try:
        manifest = prepare(args.output_dir, args.from_directory, args.source_url)
    except (OSError, ValueError, EOFError) as exc:
        print(f"Preparation failed: {exc}", file=sys.stderr)
        print("No validated dataset was prepared. Do not disable TLS/certificate checks.", file=sys.stderr)
        print(f"Official download page: {SOURCE}", file=sys.stderr)
        print("If automatic access is blocked, obtain the files through a trusted official route and use --from-directory with --source-url.", file=sys.stderr)
        return 1
    print(f"Prepared: {args.output_dir}")
    print("Validation:", manifest["validation"])
    print("Next: query this directory with evidence_sources.py --source sider --sider-dir", args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
