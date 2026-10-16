"""Build a deterministic draft report from saved FAERS and DailyMed results."""

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import faers_stats
from faers_stats import compute_statistics, validate_audit, format_stat


def load(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return value, raw, hashlib.sha256(raw).hexdigest()


def validate_inputs(audit, stats, label, audit_hash):
    table = validate_audit(audit)
    definition = audit.get("definition")
    if not isinstance(definition, dict) or not definition.get("drug") or not definition.get("event"):
        raise ValueError("Counts audit is missing the drug or event definition")
    if stats.get("status") != "completed" or stats.get("source_sha256") != audit_hash:
        raise ValueError("Statistics are incomplete or do not match this audit.json (SHA-256 mismatch)")
    if stats.get("table") != table or stats.get("definition") != definition:
        raise ValueError("Statistics table or definition does not match the counts audit")
    saved = stats.get("statistics")
    if not isinstance(saved, dict) or saved.get("method") != "log-Wald" or saved.get("continuity_correction") is not None:
        raise ValueError("Only log-Wald statistics without a continuity correction are supported")
    confidence = saved.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("Invalid confidence level in statistics file")
    computed = compute_statistics(table, confidence)
    for name in ("PRR", "ROR"):
        for key in ("estimate", "se_log", "ci_lower", "ci_upper"):
            value = saved.get(name, {}).get(key)
            if value is None and computed[name][key] is None:
                continue
            if computed[name][key] is None:
                raise ValueError(f"Expected an unavailable estimate: {name}.{key}")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isclose(value, computed[name][key], rel_tol=1e-10):
                raise ValueError(f"Statistics failed recalculation check:{name}.{key}")
    if label.get("status") != "completed":
        raise ValueError("Label input must be a completed full-text retrieval, not a candidate list")
    if str(label.get("drug_input", "")).strip().casefold() != definition["drug"].strip().casefold():
        raise ValueError("Label drug input does not match the FAERS analysis")
    detail = label.get("label")
    if not isinstance(detail, dict) or not detail.get("setid") or not isinstance(detail.get("matches"), list):
        raise ValueError("Label record is missing SETID or matches")
    for hit in detail["matches"]:
        if not isinstance(hit, dict) or not isinstance(hit.get("text"), str) or not isinstance(hit.get("section_title"), str):
            raise ValueError("Invalid label-section structure")
    return computed


def yaml_lines(value, indent=0):
    """Emit JSON-quoted YAML keys/scalars without a third-party dependency."""
    prefix = " " * indent
    if isinstance(value, dict) and value:
        lines = []
        for key, item in value.items():
            name = json.dumps(str(key), ensure_ascii=False)
            if isinstance(item, (dict, list)) and item:
                lines.append(prefix + name + ":")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                lines.append(prefix + name + ": " + json.dumps(item, ensure_ascii=False, allow_nan=False))
        return lines
    if isinstance(value, list) and value:
        lines = []
        for item in value:
            if isinstance(item, (dict, list)) and item:
                lines.append(prefix + "-")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                lines.append(prefix + "- " + json.dumps(item, ensure_ascii=False, allow_nan=False))
        return lines
    return [prefix + json.dumps(value, ensure_ascii=False, allow_nan=False)]


def md_cell(value):
    if value is None or value == "":
        return "Not reported"
    return " ".join(str(value).split()).replace("|", "&#124;").replace("<", "&lt;").replace(">", "&gt;")


def render_auxiliary(evidence):
    lines = ["## Auxiliary evidence", "",
             "These sources provide context and do not change the FAERS contingency table. Search results require relevance review.", "",
             "| Source | Status |", "|---|---|"]
    for name in ("clinical_trials", "drugsfda", "sider"):
        result = evidence.get(name, {"status": "not_supplied"})
        lines.append(f"| {name} | {md_cell(result.get('status', 'unknown'))} |")
    lines.append("")
    for name in ("clinical_trials", "drugsfda", "sider"):
        result = evidence.get(name, {"status": "not_supplied"})
        status = result.get("status", "unknown")
        lines += [f"### {name}", "", f"Status: **{md_cell(status)}**.", ""]
        if result.get("source_url"):
            lines += [f"Source: {result['source_url']}", ""]
        if status != "completed":
            lines += [md_cell(result.get("reason") or result.get("error") or
                              "No completed evidence supplied. This does not establish absence of risk or approval."), ""]
            continue
        if name == "clinical_trials":
            studies = result.get("population_context", [])
            lines += [f"Retrieved studies: {len(studies)}. Only the first search page was requested; this is not a systematic review.", "",
                      "Eligibility criteria describe permitted enrollment, not observed participant characteristics. Enrollment counts retain their registry type (for example, ESTIMATED or ACTUAL).", "",
                      "| NCT ID | Study | Age range | Sex | Healthy volunteers | Enrollment / type |",
                      "|---|---|---|---|---|---|"]
            for study in studies:
                eligibility = study.get("eligibility") or {}
                enrollment = study.get("enrollment") or {}
                healthy = eligibility.get("healthyVolunteers")
                healthy = "Yes" if healthy is True else "No" if healthy is False else "Not reported"
                row = [study.get("nct_id"), study.get("title"),
                       f"{eligibility.get('minimumAge', 'Not reported')} to {eligibility.get('maximumAge', 'Not reported')}",
                       eligibility.get("sex"), healthy,
                       f"{enrollment.get('count', 'Not reported')} / {enrollment.get('type', 'Not reported')}"]
                lines.append("| " + " | ".join(md_cell(v) for v in row) + " |")
            lines.append("")
            for study in studies:
                lines += [f"**{md_cell(study.get('nct_id'))}: intervention and eligibility excerpts**", ""]
                interventions = study.get("interventions") or []
                lines += ["- Interventions: " + ("; ".join(md_cell(item.get("name")) for item in interventions) or "Not reported")]
                criteria = (study.get("eligibility") or {}).get("eligibilityCriteria") or "Not reported"
                excerpt = criteria[:600] + (" [Excerpt truncated; see evidence.json.]" if len(criteria) > 600 else "")
                lines += ["- Eligibility excerpt: " + md_cell(excerpt), ""]
        elif name == "drugsfda":
            records = result.get("response", {}).get("results", [])
            lines += [f"Retrieved application records: {len(records)}. These may contain multiple products and combination formulations; this is not a complete approval history.", "",
                      "| Application | Sponsor | Product number | Brand | Active ingredients / strengths | Dosage form | Marketing status (as returned) |",
                      "|---|---|---|---|---|---|---|"]
            for record in records:
                for product in record.get("products") or [{}]:
                    ingredients = "; ".join(f"{item.get('name', 'Not reported')} ({item.get('strength', 'strength not reported')})"
                                            for item in product.get("active_ingredients", []))
                    row = [record.get("application_number"), record.get("sponsor_name"), product.get("product_number"),
                           product.get("brand_name"), ingredients, product.get("dosage_form"), product.get("marketing_status")]
                    lines.append("| " + " | ".join(md_cell(v) for v in row) + " |")
            lines += ["", "Application and product fields are reproduced from Drugs@FDA; they do not independently establish current availability or a complete regulatory timeline.", ""]
            lines += ["**Submission status fields (source values, not an inferred approval timeline)**", "",
                      "submission_status_date is the date the recorded submission status was applied. It is not automatically the original product approval date. Only the first 5 returned submissions per application are shown; complete records remain in evidence.json.", "",
                      "| Application | Submission type | Submission number | Status | Status date (raw YYYYMMDD) |",
                      "|---|---|---|---|---|"]
            for record in records:
                submissions = record.get("submissions") or []
                if not submissions:
                    lines.append(f"| {md_cell(record.get('application_number'))} | Not reported | Not reported | Not reported | Not reported |")
                for submission in submissions[:5]:
                    row = [record.get("application_number"), submission.get("submission_type"),
                           submission.get("submission_number"), submission.get("submission_status"),
                           submission.get("submission_status_date")]
                    lines.append("| " + " | ".join(md_cell(v) for v in row) + " |")
                if len(submissions) > 5:
                    lines.append(f"| {md_cell(record.get('application_number'))} | Additional {len(submissions) - 5} submissions omitted; see evidence.json | — | — | — |")
            lines.append("")
        else:
            lines += [f"Drug matching: {md_cell(result.get('drug_match_status'))}.",
                      f"Matching event records: {len(result.get('matches', []))}.", "",
                      "SIDER is label-derived evidence. An unmatched drug or an absent event match is not proof of no risk.", ""]
            diagnostics = result.get("diagnostics", [])
            for diagnostic in diagnostics:
                coverage = diagnostic.get("coverage", {})
                lines += ["**Identifier coverage and event-term diagnostic**", "",
                          "| Check | Result |", "|---|---|"]
                checks = [
                    ("Compound IDs matched by drug name", ", ".join(item["compound_id"] for item in diagnostic.get("drug_name_matches", [])) or "None"),
                    ("Side-effect rows for these IDs", coverage.get("drug_rows")),
                    ("Flat-ID matched rows", coverage.get("flat_id_matched_rows")),
                    ("Stereo-ID matched rows", coverage.get("stereo_id_matched_rows")),
                    ("PT rows for these IDs", coverage.get("pt_rows")),
                    ("Distinct PT terms for these IDs", coverage.get("unique_pt_terms")),
                    ("Requested event term", diagnostic.get("event")),
                    ("Exact event rows for this drug", len(diagnostic.get("exact_matches", []))),
                    ("Dataset-wide exact event rows (vocabulary check only)", coverage.get("dataset_wide_exact_event_rows")),
                    ("Candidate-search keywords", ", ".join(diagnostic.get("keywords", []))),
                    ("Candidate PT terms for this drug", len(diagnostic.get("keyword_candidates", []))),
                    ("Diagnostic finding", diagnostic.get("finding")),
                ]
                lines.extend(f"| {md_cell(check)} | {md_cell(value)} |" for check, value in checks)
                lines += ["", "Counts are database rows or distinct terms, not patients. Flat-ID and stereo-ID counts may overlap. Dataset-wide event rows are not a comparator for risk.", ""]
                candidates = diagnostic.get("keyword_candidates", [])
                if candidates:
                    lines += ["Candidate terms below require review and have not been added to the analysis:", ""]
                    lines.extend(f"- {md_cell(item['term'])}: {item['rows']} rows" for item in candidates)
                elif diagnostic.get("finding") == "exact_event_unmatched_no_keyword_candidates":
                    lines += ["The drug has PT records in these files, but neither the exact event nor the specified keyword candidates matched. This is a dataset-specific lookup result, not evidence that the clinical risk is absent.", ""]
                lines.append("")
            if not diagnostics:
                lines += ["Detailed coverage diagnostics were not supplied in this saved evidence. Re-run with the updated evidence adapter to obtain them.", ""]
            for match in result.get("matches", []):
                lines.append(f"- {md_cell(match.get('term'))}; concept: {md_cell(match.get('meddra_concept'))}")
            if result.get("manifest"):
                lines += ["", f"Dataset version: {md_cell(result['manifest'].get('version'))}.",
                          f"Dataset source: {result['manifest'].get('source_url')}", ""]
        for limitation in result.get("limitations", []):
            lines.append("- " + md_cell(limitation))
        lines.append("")
    lines += ["Full source responses, including unabridged eligibility criteria and application products, are retained in evidence.json.", ""]
    return "\n".join(lines)


def render_report(audit, computed, label, cohort_id, evidence=None):
    definition, table, detail = audit["definition"], audit["table"], label["label"]
    lines = [
        "# OpenPulse Signal Detection Report — Draft", "",
        f"Analysis definition version: `{cohort_id}`", "",
        "## Analysis definition", "",
        f"- Drug: {definition['drug']}", f"- Event: {definition['event']}",
        f"- Years: {definition.get('start_year')}–{definition.get('end_year')}",
        f"- Date field: `{definition.get('date_field')}`",
        f"- Drug field: `{definition.get('drug_field')}`",
        f"- Event field: `{definition.get('event_field')}`",
        "- Full filters and handling rules are preserved in cohort.yaml.", "",
        "## FAERS contingency table", "",
        "| | Target event matched | Target event not matched |", "|---|---:|---:|",
        f"| Target drug matched | {table['a']} | {table['b']} |",
        f"| Target drug not matched | {table['c']} | {table['d']} |", "",
        f"Target-drug event reporting proportion: {format_stat(computed['report_proportion_drug'], percent=True)}.",
        f"Background event reporting proportion: {format_stat(computed['report_proportion_background'], percent=True)}.", "",
        "## Disproportionality statistics", "",
        f"Method: log-Wald; confidence level: {computed['confidence']:.2%}; no continuity correction.", "",
        "| Metric | Estimate | CI lower | CI upper | SE(log) |", "|---|---:|---:|---:|---:|",
    ]
    for name in ("PRR", "ROR"):
        value = computed[name]
        lines.append("| " + " | ".join([name] + [format_stat(value[k]) for k in ('estimate', 'ci_lower', 'ci_upper', 'se_log')]) + " |")
    if computed.get("estimation_status") == "zero_cell_no_log_wald_interval":
        lines += ["", "A cell is zero: log-Wald confidence intervals are not estimable in this implementation. No continuity correction is applied; unavailable estimates must not be interpreted as no risk.", ""]
    lines += ["", "These are reporting disproportionality estimates, not incidence, patient risk ratios, or causal effects. No predefined signal-screening rule has been applied.", "",
              "## DailyMed label evidence", "",
              f"- SETID: `{detail['setid']}`", f"- Version: {detail.get('version')}",
              f"- Label effectiveTime: {detail.get('effective_time')} (not necessarily the publication date)",
              f"- Retrieved: {label.get('retrieved_at_utc')}",
              f"- Original label: {label.get('label_url')}", f"- Download source: {label.get('source_url')}",
              f"- Keyword: {label.get('keyword')}; matching sections: {len(detail['matches'])}.", "",
              "The excerpts below are keyword matches, not independent evidence counts or an automated risk assessment. Clinical relevance and product scope still require human review.", ""]
    product_check = label.get("product_check", {})
    if product_check.get("status") == "verified_against_catalog":
        lines += ["Product identity check: SETID, product title, and active ingredients matched the configured reference.",
                  "Verified active ingredients: " + ", ".join(product_check.get("active_ingredients", [])) + ".", ""]
    else:
        lines += ["Product identity was not automatically verified in this saved label record; review the ingredients and dosage form manually.", ""]
    if not detail["matches"]:
        lines += ["No keyword matches were extracted. This does not establish that the label omits the risk.", ""]
    for hit in detail["matches"]:
        lines += [f"### {hit['section_title']}", ""]
        lines.extend("> " + line for line in hit["text"].splitlines())
        lines.append("")
    lines += ["## Limitations and pending checks", "",
              "- Standardized generic-name fields may be missing. Phrase matching does not guarantee complete or accurate drug identification.",
              "- Only the selected event term is queried; a complete synonym or related-term set is not included.",
              "- openFDA documentation states that only the latest version of a report is returned. Duplicate cases across different report identifiers have not been independently addressed.",
              "- receivedate is the first FDA receipt date, not event onset. Current report contents may include updates after the selected years; this is not a historical frozen snapshot.",
              "- Separate API requests are not an atomic snapshot; database updates may affect consistency.",
              "- Confidence intervals depend on the independent-count, large-sample approximation and do not capture systematic reporting biases.",
              "- Current labeling does not establish historical label content during the analysis years.",
              "- Keyword absence does not establish risk absence. XML extraction may lose table formatting; check the original label.",
              "- Complete event harmonization remains pending. Auxiliary source availability is reported below when evidence is supplied.",
              "- Primary results use a fixed template. Any separately included model synthesis requires human review.",
              "- Saved count responses permit statistical recalculation, but are not a snapshot of all FAERS reports. A future API query may yield different counts.",
              "- Original source-specific notes and definitions are preserved verbatim in the input JSON copies, including their original language."]
    if min(table.values()) < 5:
        lines.append("- At least one cell count is below 5; the large-sample approximation may be unreliable.")
    if evidence is not None:
        lines += ["", render_auxiliary(evidence)]
    else:
        lines += ["", "## Auxiliary evidence", "", "No auxiliary evidence file was supplied to this report generator.", ""]
    lines += ["", "## Reproduction", "",
              "The analysis directory preserves source JSON files and provenance.json. Label evidence is stored as label.json in standalone reports, or label_result.json in workflow runs.",
              "Re-run faers_stats.py using the copied audit.json. cohort.yaml preserves the versioned analysis definition.",
              "Software: Python standard library; build_report.py and faers_stats.py.", ""]
    return "\n".join(lines)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--label", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, help="Optional workflow evidence.json or standalone evidence_sources.py output")
    parser.add_argument("--output-dir", type=Path, help="New output directory; existing directories are not overwritten")
    args = parser.parse_args()
    try:
        loaded = {name: load(path) for name, path in (("audit", args.audit), ("stats", args.stats), ("label", args.label))}
        audit, stats, label = (loaded[name][0] for name in ("audit", "stats", "label"))
        computed = validate_inputs(audit, stats, label, loaded["audit"][2])
        evidence = None
        if args.evidence:
            loaded["evidence"] = load(args.evidence)
            evidence_data = loaded["evidence"][0]
            evidence = evidence_data.get("sources", evidence_data)
            if not isinstance(evidence, dict) or any(not isinstance(v, dict) for v in evidence.values()):
                raise ValueError("Invalid auxiliary evidence structure")
            evidence = { {"trials": "clinical_trials", "approval": "drugsfda"}.get(k, k): v for k, v in evidence.items() }
        now = datetime.now(timezone.utc)
        folder = args.output_dir or Path("data") / ("report_" + now.strftime("%Y%m%dT%H%M%S%fZ"))
        cohort_core = {"schema_version": "1.0.0", "analysis": audit["definition"],
                       "queries": audit.get("queries", {}),
                       "statistical_method": {"method": computed["method"], "confidence": computed["confidence"], "continuity_correction": None}}
        cohort_id = hashlib.sha256(json.dumps(cohort_core, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        cohort = {"cohort_version": cohort_id, **cohort_core}
        folder.mkdir(parents=True, exist_ok=False)
        for name, (_, raw, _) in loaded.items():
            (folder / (name + ".json")).write_bytes(raw)
        provenance = {"generated_at_utc": now.isoformat(), "generator_version": "1.1.0",
                      "cohort_version": cohort_id,
                      "inputs": {name: {"file": name + ".json", "sha256": item[2]} for name, item in loaded.items()},
                      "code_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                      for path in (Path(__file__), Path(faers_stats.__file__))}}
        (folder / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
        (folder / "cohort.yaml").write_text("\n".join(yaml_lines(cohort)) + "\n", encoding="utf-8")
        (folder / "report.md").write_text(render_report(audit, computed, label, cohort_id, evidence=evidence), encoding="utf-8")
    except (OSError, ValueError, TypeError, AttributeError, OverflowError) as exc:
        print(f"Failed:{exc}; any partial output directory must not be treated as a completed report.", file=sys.stderr)
        return 1
    print(f"Report:{folder / 'report.md'}")
    print(f"Analysis definition:{folder / 'cohort.yaml'}")
    print("Input correspondence and statistical recalculation verified. Label interpretation and FAERS methodological review still require human assessment.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
