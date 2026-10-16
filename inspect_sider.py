"""Inspect SIDER identifier coverage and candidate event terms without changing an analysis."""

import argparse
import csv
import gzip
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(directory, drug, event, keywords):
    names = directory / "drug_names.tsv"
    events = directory / "meddra_all_se.tsv.gz"
    manifest_file = directory / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")
    hashes = {path.name: file_hash(path) for path in (names, events, manifest_file)}
    manifest_hash_status = {}
    for path in (names, events):
        expected = manifest.get("files", {}).get(path.name, {}).get("sha256")
        if expected and expected != hashes[path.name]:
            raise ValueError(f"File hash does not match the saved manifest: {path.name}")
        manifest_hash_status[path.name] = "matched" if expected else "not_provided"

    drug_matches = []
    with names.open(encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) < 2:
                raise ValueError("Invalid drug_names.tsv row")
            if row[1].strip().casefold() == drug.casefold():
                drug_matches.append({"compound_id": row[0], "name": row[1]})
    identifiers = {row["compound_id"] for row in drug_matches}
    exact = []
    candidates = {}
    all_terms = set()
    drug_rows = flat_rows = stereo_rows = pt_rows = 0
    global_exact_rows = 0
    for_keyword = [word.casefold() for word in keywords]
    with gzip.open(events, "rt", encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) < 6:
                raise ValueError("Invalid side-effect row: expected at least six columns")
            if row[3] == "PT" and row[5].strip().casefold() == event.casefold():
                global_exact_rows += 1
            flat_match = row[0] in identifiers
            stereo_match = row[1] in identifiers
            if not (flat_match or stereo_match):
                continue
            drug_rows += 1
            flat_rows += int(flat_match)
            stereo_rows += int(stereo_match)
            if row[3] != "PT":
                continue
            pt_rows += 1
            term = row[5].strip()
            all_terms.add(term)
            record = {"flat_compound_id": row[0], "stereo_compound_id": row[1],
                      "meddra_concept": row[4], "term": term}
            if term.casefold() == event.casefold():
                exact.append(record)
            if any(word in term.casefold() for word in for_keyword):
                candidates.setdefault(term, {"term": term, "rows": 0, "meddra_concepts": set()})
                candidates[term]["rows"] += 1
                candidates[term]["meddra_concepts"].add(row[4])
    if not identifiers:
        finding = "drug_name_unmatched"
    elif drug_rows == 0:
        finding = "drug_name_matched_but_no_side_effect_rows"
    elif pt_rows == 0:
        finding = "drug_rows_present_but_no_pt_rows"
    elif exact:
        finding = "exact_event_matched"
    elif candidates:
        finding = "exact_event_unmatched_candidate_terms_found"
    else:
        finding = "exact_event_unmatched_no_keyword_candidates"
    return {
        "status": "completed", "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "drug": drug, "event": event, "keywords": keywords,
        "dataset_version": manifest.get("version", "unknown"), "source_url": manifest.get("source_url"),
        "files_sha256": hashes, "saved_manifest_hash_check": manifest_hash_status,
        "drug_name_matches": drug_matches,
        "coverage": {"drug_rows": drug_rows, "flat_id_matched_rows": flat_rows,
                     "stereo_id_matched_rows": stereo_rows, "pt_rows": pt_rows,
                     "unique_pt_terms": len(all_terms), "dataset_wide_exact_event_rows": global_exact_rows},
        "finding": finding, "exact_matches": exact,
        "keyword_candidates": [{**item, "meddra_concepts": sorted(item["meddra_concepts"])}
                               for _, item in sorted(candidates.items())],
        "all_drug_pt_terms": sorted(all_terms),
        "limitations": [
            "Keyword candidates are not validated synonyms and are not automatically added to the analysis.",
            "Name-table matching does not guarantee the same identifier has side-effect records.",
            "These checks do not resolve every identifier-mapping or release-compatibility problem.",
            "Dataset-wide exact event rows are only a vocabulary diagnostic, not a risk comparator.",
            "Row counts are database entries, not patients or FAERS reports. Flat and stereo counts can overlap.",
            "No match does not establish absence of risk. No source files or FAERS results are modified.",
            "Locally recorded hashes identify files; they are not independent publisher verification.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sider-dir", type=Path, default=Path("data/sider_local"))
    parser.add_argument("--drug", default="empagliflozin")
    parser.add_argument("--event", default="Diabetic ketoacidosis")
    parser.add_argument("--keyword", action="append", help="Repeat for multiple substring searches; diagnostic only")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    keywords = args.keyword or ["ketoacidosis", "ketoacid", "ketosis"]
    if not args.drug.strip() or not args.event.strip() or any(not word.strip() for word in keywords):
        parser.error("Drug, event, and keywords must not be empty")
    try:
        result = inspect(args.sider_dir, args.drug.strip(), args.event.strip(), [word.strip() for word in keywords])
        folder = args.output_dir / ("sider_inspection_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        folder.mkdir(parents=True, exist_ok=False)
        output = folder / "inspection.json"
        with output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
    except (OSError, ValueError, EOFError) as exc:
        print(f"Inspection failed: {exc}", file=sys.stderr)
        return 1
    print("Dataset version:", result["dataset_version"])
    print("Drug-name matches:", result["drug_name_matches"])
    print("Coverage:", result["coverage"])
    print("Exact event matches:", len(result["exact_matches"]))
    print("Finding:", result["finding"])
    print("Keyword candidates (not validated synonyms):")
    for item in result["keyword_candidates"]:
        print(f"  {item['term']} | rows={item['rows']} | concepts={', '.join(item['meddra_concepts'])}")
    if not result["keyword_candidates"]:
        print("  None found")
    print("Saved:", output)
    print("Diagnostic only: no event definitions, dataset files, or FAERS results were changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
