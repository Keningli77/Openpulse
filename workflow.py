"""Deterministic workflow shared by the web form and tests."""

import argparse
import sys
import hashlib
import io
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from build_report import render_report, validate_inputs, yaml_lines
from dailymed_label import BASE, NS, extract_sections, get_bytes
from evidence_sources import get_approval_metadata, get_sider_side_effects, get_trial_population
from faers_counts import build_queries, fetch_total, make_table
from faers_stats import compute_statistics, format_stat
from runtime_config import get_gemini_model

ROOT = Path(__file__).resolve().parent


def read_catalog():
    return json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))


def save_json(path, data):
    raw = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    with path.open("xb") as handle:
        handle.write(raw)
    return raw


def synthesis_input(audit, computed, label, evidence):
    """Prepare explicit source scope; do not hide a subset behind a global claim."""
    trials = evidence["clinical_trials"].get("population_context", [])
    records = evidence["drugsfda"].get("response", {}).get("results", [])
    approvals = []
    for record in records:
        approvals.append({
            "application_number": record.get("application_number"),
            "sponsor_name": record.get("sponsor_name"),
            "products": [{key: product.get(key) for key in
                          ("product_number", "brand_name", "active_ingredients", "dosage_form", "marketing_status")}
                         for product in record.get("products", [])],
            "regulatory_timeline_assessment": "Not assessed. Do not state approval dates in the synthesis.",
        })
    compact_trials = []
    for trial in trials:
        eligibility = trial.get("eligibility") or {}
        criteria = eligibility.get("eligibilityCriteria", "")
        compact_trials.append({
            "nct_id": trial.get("nct_id"), "title": trial.get("title"),
            "intervention_names": [item.get("name") for item in trial.get("interventions", [])],
            "eligibility": {key: eligibility.get(key) for key in
                            ("minimumAge", "maximumAge", "sex", "healthyVolunteers")},
            "eligibility_excerpt": criteria[:600], "eligibility_excerpt_truncated": len(criteria) > 600,
            "enrollment": trial.get("enrollment"),
        })
    enrollment_types = {}
    for trial in trials:
        kind = (trial.get("enrollment") or {}).get("type") or "NOT_REPORTED"
        enrollment_types[kind] = enrollment_types.get(kind, 0) + 1
    return {
        "definition": audit["definition"], "table": audit["table"], "statistics": computed,
        "counting_unit": "FAERS reports, not unique patients or confirmed cases",
        "source_registry": {
            "faers": {"url": "https://api.fda.gov/drug/event.json", "status": "completed"},
            "dailymed": {"url": label["label_url"], "status": "completed"},
            **{name: {"status": result["status"], "url": result.get("source_url") or result.get("manifest", {}).get("source_url")}
               for name, result in evidence.items()},
        },
        "sampling_scope": {
            "trials_retrieved": len(trials), "trials_supplied_to_model": len(compact_trials),
            "enrollment_type_counts_in_retrieved_trials": enrollment_types,
            "applications_retrieved": len(records), "applications_supplied_to_model": len(approvals),
            "label_matched_sections": len(label["label"]["matches"]),
            "label_sections_supplied": min(3, len(label["label"]["matches"])),
            "limits": "Only the first API search page, not all trials or applications. Trial eligibility excerpts are limited to 600 characters; label excerpts to 4000 characters. Do not generalize missing data to the full registry.",
        },
        "label": {"source": label["label_url"], "version": label["label"]["version"],
                  "effective_time": label["label"]["effective_time"],
                  "matches": [{"section_title": item["section_title"], "text": item["text"][:4000],
                               "excerpt_truncated": len(item["text"]) > 4000}
                              for item in label["label"]["matches"][:3]]},
        "source_status": {name: result["status"] for name, result in evidence.items()},
        "trial_context": compact_trials, "approval_records": approvals,
        "sider": {k: v for k, v in evidence["sider"].items() if k != "files_sha256"},
    }


def fetch_verified_label(drug, event, folder):
    setid = drug["label_setid"]
    url = BASE + "downloadzipfile.cfm?" + urlencode({"setId": setid})
    raw = get_bytes(url)
    (folder / "label.zip").write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        candidates = [item for item in archive.infolist() if item.filename.lower().endswith(".xml")]
        if len(candidates) != 1 or candidates[0].file_size > 32 * 1024 * 1024:
            raise ValueError("Unexpected label XML count or size")
        xml = archive.read(candidates[0])
    parsed = extract_sections(xml, event["label_keyword"])
    if str(parsed["setid"]).casefold() != setid.casefold():
        raise ValueError("Label SETID mismatch")
    root = ET.fromstring(xml)
    # SPL active ingredient codes, excluding IACT (inactive ingredients).
    active = set()
    for ingredient in root.findall(".//s:ingredient", NS):
        if ingredient.get("classCode") in {"ACTIB", "ACTIM", "ACTIR"}:
            for name in ingredient.findall("s:ingredientSubstance/s:name", NS):
                active.add(" ".join(name.itertext()).strip().casefold())
    expected = {name.casefold() for name in drug["reference_ingredients"]}
    if active != expected:
        raise ValueError(f"Label active ingredients do not match the catalog; expected {sorted(expected)}; found {sorted(active)}")
    title = root.find("s:title", NS)
    title_text = " ".join(title.itertext()) if title is not None else ""
    if drug["reference_product"].casefold() not in title_text.casefold():
        raise ValueError("Label title does not match the reference product; manual review required")
    (folder / "label.xml").write_bytes(xml)
    return {
        "status": "completed", "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "drug_input": None, "keyword": event["label_keyword"],
        "source_url": url, "label_url": drug["mapping_source"], "label": parsed,
        "product_check": {"title": title_text, "active_ingredients": sorted(active),
                          "status": "verified_against_catalog"},
        "limitations": ["The selected product label is contextual evidence, not labeling for every product containing the query ingredient.",
                        "Current labeling does not establish historical labeling; keyword matches do not establish causality."],
    }


def run_analysis(drug_key, event_key, start_year, end_year, *, include_trials=True,
                 include_approval=True, sider_directory=None, use_gemini=False,
                 progress=lambda message: None,
                 output_root=None, drug_selection=None):
    catalog = read_catalog()
    if event_key not in catalog["events"]:
        raise ValueError("Select one of the defined event terms; approximate event matching is not performed")
    if drug_selection is not None:
        if drug_key not in drug_selection.get("query_ingredients", []):
            raise ValueError("The query ingredient is not supported by the selected label")
        drug = drug_selection
    elif drug_key in catalog["drugs"]:
        drug = catalog["drugs"][drug_key]
    else:
        raise ValueError("Search and confirm a drug product before analysis")
    event = catalog["events"][event_key]
    queries = build_queries(drug_key, event["faers_term"], start_year, end_year)
    model = get_gemini_model() if use_gemini else None
    now = datetime.now(timezone.utc)
    folder = Path(output_root or ROOT / "data") / ("web_" + now.strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True, exist_ok=False)
    run = {"status": "running", "started_at_utc": now.isoformat(), "sources": {}}
    try:
        audit = {
            "status": "running", "started_at_utc": now.isoformat(),
            "definition": {"drug": drug_key, "event": event["faers_term"],
                           "start_year": start_year, "end_year": end_year, "date_field": "receivedate",
                           "drug_field": "patient.drug.openfda.generic_name",
                           "event_field": "patient.reaction.reactionmeddrapt.exact",
                           "age_sex_filters": None, "drug_role_filter": None,
                           "deduplication": "Latest version per report according to openFDA documentation; no cross-report case deduplication",
                           "catalog_version": catalog["schema_version"], "faers_scope": drug["faers_scope"],
                           "reference_product": drug["reference_product"], "reference_label_setid": drug["label_setid"],
                           "reference_ingredients": drug["reference_ingredients"],
                           "mapping_source": drug["mapping_source"]},
            "queries": queries, "requests": {},
            "limitations": ["Standardized generic-name matching can miss or misidentify records; matching sensitivity review remains pending.",
                            "Reports first received during the selected years, using their current latest contents; not a historical frozen snapshot.",
                            "Duplicate cases across reports were not independently resolved; no suspect-drug role restriction.",
                            "Four queries are not an atomic snapshot; only count responses and samples are saved, not all reports.",
                            "One full event term is queried, not a complete synonym set."],
        }
        for name, query in queries.items():
            progress(f"FAERS: querying {name}")
            audit["requests"][name] = fetch_total(query)
        totals = {name: value["total"] for name, value in audit["requests"].items()}
        table = make_table(totals)
        if totals["N"] == 0:
            raise ValueError("No reports found for the selected years")
        audit.update(status="completed", totals=totals, table=table)
        audit_raw = save_json(folder / "audit.json", audit)
        run["sources"]["faers"] = "completed"
        progress("Computing PRR/ROR and confidence intervals")
        computed = compute_statistics(table)
        stats = {"status": "completed", "source_sha256": hashlib.sha256(audit_raw).hexdigest(),
                 "definition": audit["definition"], "table": table, "statistics": computed,
                 "source_limitations": audit["limitations"]}
        save_json(folder / "stats.json", stats)
        progress("DailyMed: downloading label and verifying active ingredients")
        label = fetch_verified_label(drug, event, folder)
        label["drug_input"] = drug_key
        save_json(folder / "label_result.json", label)
        run["sources"]["dailymed"] = "completed"

        evidence = {}
        def optional(name, enabled, function):
            progress(f"Auxiliary source:{name}")
            if not enabled:
                result = {"status": "skipped", "reason": "Not enabled for this run"}
            else:
                try:
                    result = function()
                except Exception as exc:
                    result = {"status": "failed", "error": str(exc)}
            evidence[name] = result
            run["sources"][name] = result["status"]
        optional("clinical_trials", include_trials, lambda: get_trial_population(drug_key))
        optional("drugsfda", include_approval, lambda: get_approval_metadata(drug_key))
        optional("sider", True, lambda: get_sider_side_effects(drug_key, event["sider_terms"], sider_directory))
        save_json(folder / "evidence.json", evidence)
        save_json(folder / "catalog_snapshot.json", catalog)
        save_json(folder / "drug_selection.json", drug)
        verified = validate_inputs(audit, stats, label, hashlib.sha256(audit_raw).hexdigest())
        cohort_core = {"schema_version": "1.0.0", "analysis": audit["definition"],
                       "queries": queries, "catalog": catalog,
                       "statistics": {"method": "log-Wald", "confidence": 0.95}}
        version = hashlib.sha256(json.dumps(cohort_core, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        (folder / "cohort.yaml").write_text("\n".join(yaml_lines({"cohort_version": version, **cohort_core})) + "\n", encoding="utf-8")
        report = render_report(audit, verified, label, version, evidence=evidence)
        progress("Generating report and downloadable analysis bundle")
        ai_input = synthesis_input(audit, computed, label, evidence)
        if use_gemini:
            progress("Gemini: generating an English synthesis appendix")
            save_json(folder / "gemini_input.json", ai_input)
            try:
                from gemini_summary import generate_summary
                ai = generate_summary(ai_input)
            except Exception as exc:
                ai = {"status": "failed", "model": model, "error": str(exc)}
        else:
            ai = {"status": "skipped", "reason": "Gemini is disabled; the fixed-template report remains available."}
        save_json(folder / "gemini.json", ai)
        if use_gemini:
            save_json(folder / "gemini_settings_snapshot.json", {
                "configuration_source": "backend_settings.json", "model": ai.get("model", model),
            })
        run["sources"]["gemini"] = ai["status"]
        report += "\n## Gemini auxiliary synthesis\n\n"
        if ai.get("model"):
            report += f"Configured model: `{ai['model']}`.\n\n"
        if ai["status"] in {"completed", "review_required"}:
            if ai.get("validation_issues"):
                report += "Automated review flags (the synthesis is not accepted as validated):\n\n"
                report += "\n".join("- " + item for item in ai["validation_issues"]) + "\n\n"
            report += "The following appendix is model-generated. Narrative accuracy has not been automatically validated; human review is required.\n\n" + ai["text"] + "\n"
            report += "\nEvidence IDs refer to the FAERS, DailyMed, and auxiliary evidence sections above. The exact submitted excerpts are retained in gemini_input.json.\n"
        else:
            report += f"Status:{ai['status']}. The fixed-template report and statistics are retained.\n"
            if ai.get("reason"):
                report += "\nReason: " + ai["reason"] + "\n"
        (folder / "report.md").write_text(report, encoding="utf-8")
        files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in folder.iterdir() if path.is_file()}
        code = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob("*.py")}
        save_json(folder / "provenance.json", {"cohort_version": version, "files_sha256": files,
                                                "code_sha256": code, "catalog_sha256": hashlib.sha256((ROOT / 'catalog.json').read_bytes()).hexdigest()})
        run.update(status="completed", finished_at_utc=datetime.now(timezone.utc).isoformat())
        save_json(folder / "run.json", run)
        bundle = folder / "analysis.zip"
        with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in folder.iterdir():
                if path.is_file() and path != bundle:
                    archive.write(path, path.name)
        return {"folder": folder, "report": report, "statistics": computed,
                "table": table, "sources": run["sources"], "bundle": bundle}
    except Exception as exc:
        run.update(status="failed", error=str(exc))
        save_json(folder / "run.json", run)
        raise RuntimeError(f"Analysis incomplete: {exc}. Diagnostic record: {folder / 'run.json'}") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drug", default="empagliflozin", help="Drug key in catalog.json")
    parser.add_argument("--event", default="dka", help="Event key in catalog.json")
    parser.add_argument("--start-year", type=int, default=2022)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--skip-trials", action="store_true")
    parser.add_argument("--skip-approval", action="store_true")
    parser.add_argument("--sider-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--use-gemini", action="store_true")
    args = parser.parse_args()
    try:
        result = run_analysis(
            args.drug, args.event, args.start_year, args.end_year,
            include_trials=not args.skip_trials,
            include_approval=not args.skip_approval,
            sider_directory=args.sider_dir,
            use_gemini=args.use_gemini,
            output_root=args.output_dir,
            progress=lambda message: print(message, flush=True),
        )
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1
    print("\nCore analysis completed. Review auxiliary source statuses separately.")
    print("Source statuses:", json.dumps(result["sources"]))
    for name in ("PRR", "ROR"):
        item = result["statistics"][name]
        print(f"{name} = {format_stat(item['estimate'])}; 95% CI [{format_stat(item['ci_lower'])}, {format_stat(item['ci_upper'])}]")
    print(f"Report: {result['folder'] / 'report.md'}")
    print(f"Cohort definition: {result['folder'] / 'cohort.yaml'}")
    print(f"Download bundle: {result['bundle']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
