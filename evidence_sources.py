"""Evidence adapters. Failed, skipped and empty results stay distinct."""

import argparse
import csv
import gzip
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import urlopen


def request_json(base, params):
    url = base + "?" + urlencode(params)
    try:
        with urlopen(url, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code != 404:
            raise
        payload = json.loads(exc.read())
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        if error.get("code") != "NOT_FOUND" or error.get("message") != "No matches found!":
            raise
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object from the evidence API")
    return {"source_url": url, "response": payload}


def validate_drug(drug):
    drug = drug.strip()
    if not drug or any(char in drug for char in ('"', '\\')):
        raise ValueError("Provide a nonempty drug name without quotes or backslashes")
    return drug


def get_trial_population(drug):
    drug = validate_drug(drug)
    data = request_json("https://clinicaltrials.gov/api/v2/studies", {
        "query.intr": drug, "pageSize": 5, "format": "json", "countTotal": "true",
    })
    studies = data["response"].get("studies")
    if not isinstance(studies, list):
        raise ValueError("ClinicalTrials.gov did not return a studies list")
    context = []
    for study in studies:
        protocol = study.get("protocolSection", {})
        identity = protocol.get("identificationModule", {})
        context.append({
            "nct_id": identity.get("nctId"), "title": identity.get("briefTitle"),
            "interventions": protocol.get("armsInterventionsModule", {}).get("interventions", []),
            "eligibility": protocol.get("eligibilityModule", {}),
            "enrollment": protocol.get("designModule", {}).get("enrollmentInfo"),
        })
    return {"status": "completed", **data, "population_context": context,
            "limitations": ["Only the first 5 search results are retrieved, not a systematic review. Verify intervention relevance. Eligibility criteria do not describe the actual enrolled population."]}


def get_approval_metadata(drug):
    drug = validate_drug(drug)
    # Drugs@FDA product metadata, not the full prescribing label.
    data = request_json("https://api.fda.gov/drug/drugsfda.json", {
        "search": f'products.active_ingredients.name:"{drug}"', "limit": 5,
    })
    if data["response"].get("error", {}).get("code") == "NOT_FOUND":
        return {"status": "no_matches", **data,
                "limitations": ["No records matched this query. This does not establish that the drug has no approval."]}
    if not isinstance(data["response"].get("results"), list):
        raise ValueError("Drugs@FDA did not return a results list")
    return {"status": "completed", **data,
            "limitations": ["Only the first 5 application records are retrieved. Results may include combination products and are not a complete approval history or full prescribing label."]}


def get_sider_side_effects(drug, event_terms, directory):
    drug = validate_drug(drug)
    if directory is None:
        return {"status": "skipped", "reason": "No local SIDER directory configured. This does not establish absence of a side effect."}
    directory = Path(directory)
    names_path = directory / "drug_names.tsv"
    events_path = directory / "meddra_all_se.tsv.gz"
    manifest_path = directory / "manifest.json"
    if not all(path.is_file() for path in (names_path, events_path, manifest_path)):
        return {"status": "unavailable", "reason": "Missing drug_names.tsv, meddra_all_se.tsv.gz, or manifest.json"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not manifest.get("version") or not manifest.get("source_url"):
        raise ValueError("SIDER manifest must include version and source_url")
    # Reuse the diagnostic that was independently run on the local dataset.
    from inspect_sider import inspect
    if not event_terms or any(not isinstance(term, str) or not term.strip() for term in event_terms):
        raise ValueError("Provide at least one nonempty event term")
    diagnostics = []
    for term in dict.fromkeys(event_terms):
        keywords = (["ketoacidosis", "ketoacid", "ketosis"]
                    if "ketoacidosis" in term.casefold() else [term])
        diagnostics.append(inspect(directory, drug, term.strip(), keywords))
    first = diagnostics[0]
    matches = []
    for diagnostic in diagnostics:
        for match in diagnostic["exact_matches"]:
            matches.append({"compound_id": match["flat_compound_id"],
                            "meddra_concept": match["meddra_concept"], "term": match["term"]})
    return {
        "status": "completed", "manifest": manifest,
        "drug_match_status": "matched" if first["drug_name_matches"] else "unmatched",
        "drug_row_count": first["coverage"]["drug_rows"], "matches": matches,
        "files_sha256": first["files_sha256"],
        "diagnostics": diagnostics,
        "limitations": [
            "Exact generic-name and specified PT matching is used. No match does not establish absence of risk.",
            "Keyword candidates are diagnostic only, not validated synonyms; they do not change the formal event definition.",
            "SIDER is label-derived evidence, not independent confirmation of causality.",
            "Dataset release remains as recorded in the manifest; local hashes do not independently verify a publisher release.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drug", default="empagliflozin")
    parser.add_argument("--event", default="Diabetic ketoacidosis", help="Exact SIDER PT term")
    parser.add_argument("--source", choices=["all", "trials", "approval", "sider"], default="all")
    parser.add_argument("--sider-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    try:
        drug = validate_drug(args.drug)
        if not args.event.strip():
            raise ValueError("Event must not be empty")
    except ValueError as exc:
        parser.error(str(exc))
    now = datetime.now(timezone.utc)
    folder = args.output_dir / ("evidence_" + now.strftime("%Y%m%dT%H%M%S%fZ"))
    tasks = {
        "trials": lambda: get_trial_population(drug),
        "approval": lambda: get_approval_metadata(drug),
        "sider": lambda: get_sider_side_effects(drug, [args.event.strip()], args.sider_dir),
    }
    results = {}
    for name, function in tasks.items():
        if args.source not in ("all", name):
            continue
        print(f"Querying {name}...", flush=True)
        try:
            result = function()
        except (OSError, ValueError, TypeError, EOFError) as exc:
            result = {"status": "failed", "error": str(exc)}
        results[name] = result
        print(f"  Status: {result['status']}")
        if name == "trials" and result["status"] == "completed":
            context = result["population_context"]
            print(f"  Retrieved studies: {len(context)}")
            for study in context:
                print(f"  {study['nct_id']}: {study['title']}")
        if name == "approval" and result["status"] == "completed":
            records = result["response"]["results"]
            print(f"  Retrieved application records: {len(records)}")
            for record in records:
                print(f"  Application: {record.get('application_number')}; sponsor: {record.get('sponsor_name')}")
        if name == "sider" and result["status"] == "completed":
            print(f"  Drug matching: {result['drug_match_status']}; event matches: {len(result['matches'])}")
            for diagnostic in result.get("diagnostics", []):
                print("  Coverage:", diagnostic["coverage"])
                print("  Finding:", diagnostic["finding"])
        if result.get("error") or result.get("reason"):
            print(" ", result.get("error") or result.get("reason"))
    has_errors = any(item["status"] in {"failed", "unavailable"} for item in results.values())
    record = {
        "status": "completed_with_issues" if has_errors else "completed",
        "retrieved_at_utc": now.isoformat(), "drug": drug,
        "sider_event_term": args.event.strip(), "sources": results,
        "limitations": ["Auxiliary evidence does not change FAERS contingency counts or establish causality.",
                        "First-page search results require relevance review. Skipped, failed, unmatched, and empty results are not equivalent."],
    }
    try:
        folder.mkdir(parents=True, exist_ok=False)
        output = folder / "evidence.json"
        with output.open("x", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
    except OSError as exc:
        print(f"Could not save results: {exc}", file=sys.stderr)
        return 1
    print(f"Saved: {output}")
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
