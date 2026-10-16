"""Public Streamlit MVP: search a product, verify its ingredients, then analyze."""
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from drug_search import resolve_label, search_labels
from faers_stats import format_stat
from runtime_config import get_gemini_model
from workflow import read_catalog, run_analysis

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="OpenPulse | Drug safety signals", page_icon="🧬", layout="wide")


def setting(name, default=""):
    if os.environ.get(name):
        return os.environ[name]
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


key = setting("GEMINI_API_KEY")
if key:
    os.environ["GEMINI_API_KEY"] = key
allow_gemini = setting("ENABLE_GEMINI", "false").lower() == "true" and bool(key)
sider_path = setting("SIDER_DATA_DIR")
if not sider_path and (ROOT / "data/sider_local/manifest.json").is_file():
    sider_path = str(ROOT / "data/sider_local")


@st.cache_data(ttl=600, max_entries=64, show_spinner=False)
def cached_search(name, page):
    return search_labels(name, page)


@st.cache_data(ttl=600, max_entries=64, show_spinner=False)
def cached_identity(setid):
    return resolve_label(setid)


st.title("OpenPulse")
st.write("Explore drug–event reporting patterns with FAERS, drug labels, and supporting evidence.")
st.caption("Research MVP · Exploratory analysis · Not medical advice")
st.info("PRR and ROR describe reporting disproportionality—not incidence, patient risk ratios, or proof of causality. Drug matching and dataset coverage have limitations.")
live_tab, example_tab, about_tab = st.tabs(["Live analysis", "Saved example", "About & limitations"])
with example_tab:
    st.subheader("Previously generated example: empagliflozin–DKA")
    st.write("A saved run is available even if public APIs are temporarily unavailable. It is not a fresh analysis or a validation benchmark.")
    example = ROOT / "examples/empagliflozin_dka_report.md"
    if example.is_file():
        example_text = example.read_text(encoding="utf-8")
        st.download_button("Download saved example", example_text, file_name="openpulse_saved_example.md")
        with st.expander("Read saved example"):
            st.markdown(example_text)
    else:
        st.write("No saved example was included in this installation.")
with about_tab:
    st.markdown("""
**Workflow:** search DailyMed products, verify ingredients from label XML, query FAERS,
compute PRR/ROR and log-Wald intervals, and download the report and provenance.

**Scope:** product search is open, but ingredients must be confirmed from a label.
Events are three single-term queries, not complete MedDRA harmonization. Label-derived
ingredient names do not guarantee complete FAERS matching. Ingredient-level cohorts
may contain both single and combination products. Zero cells are not automatically corrected.

**Evidence:** current labels are not historical labels. Trial and application searches
return limited first-page results. SIDER is optional; an absent match is not proof of no risk.

**AI:** optional Gemini synthesis summarizes collected evidence, not autonomous tool calls.
Public evidence excerpts are sent to Google only when explicitly enabled. Narrative needs review.
""")
with live_tab:
    st.subheader("1. Search a drug product")
    with st.form("search_form"):
        name = st.text_input("Generic or brand name", value="empagliflozin", placeholder="For example: dapagliflozin or FARXIGA")
        page = st.number_input("Search results page", min_value=1, max_value=100, value=1)
        search_clicked = st.form_submit_button("Search products")
    if search_clicked:
        for state_key in ("search_result", "confirmed_identity", "analysis_result"):
            st.session_state.pop(state_key, None)
        try:
            with st.spinner("Searching DailyMed..."):
                st.session_state["search_result"] = cached_search(name.strip(), int(page))
        except Exception as exc:
            st.error(f"Drug search could not complete: {exc}. Try another name or use the saved example.")
    found = st.session_state.get("search_result")
    if found is not None:
        candidates = found["candidates"]
        st.caption(f"Search: {found['query']} · {len(candidates)} candidates on this page. Results may be repackaged or combination products.")
        if not candidates:
            st.warning("No candidates on this page. Try another name or page; this does not establish absence of a drug or risk.")
        else:
            choices = {item["setid"]: item for item in candidates}
            selected = st.selectbox("Choose a reference product label", list(choices), format_func=lambda sid: f"{choices[sid]['title']} | {choices[sid].get('published_date', 'date not reported')} | {sid[:8]}")
            identity = st.session_state.get("confirmed_identity")
            if identity and identity["label_setid"] != selected:
                st.session_state.pop("confirmed_identity", None)
                st.session_state.pop("analysis_result", None)
            if st.button("Read label ingredients"):
                st.session_state.pop("confirmed_identity", None)
                st.session_state.pop("analysis_result", None)
                try:
                    with st.spinner("Downloading label and resolving active ingredients..."):
                        st.session_state["confirmed_identity"] = cached_identity(selected)
                except Exception as exc:
                    st.error(f"Could not verify product identity: {exc}. No drug mapping was assumed.")
    identity = st.session_state.get("confirmed_identity")
    if identity:
        st.subheader("2. Confirm the analysis definition")
        st.write("Reference label:", identity["reference_product"])
        st.write("Active ingredient substances:", ", ".join(identity["reference_ingredients"]))
        st.link_button("Open original label", identity["mapping_source"])
        st.caption("Select one ingredient/active moiety. The FAERS cohort may include other single or combination products containing it.")
        catalog = read_catalog()
        with st.form("analysis_form"):
            ingredient = st.selectbox("Ingredient / active moiety to analyze", identity["query_ingredients"])
            event_key = st.selectbox("Event (single defined term)", list(catalog["events"]), format_func=lambda k: catalog["events"][k]["display_name"])
            st.caption("Exact event terms: Diabetic ketoacidosis; Urinary tract infection; Lower limb amputation.")
            cols = st.columns(2)
            year = datetime.now(timezone.utc).year
            start = cols[0].number_input("First FDA receipt: start year", min_value=2004, max_value=year, value=2022)
            end = cols[1].number_input("End year", min_value=2004, max_value=year, value=2024)
            trials = st.checkbox("Include trial-population context", value=True)
            approval = st.checkbox("Include application and product records", value=True)
            st.caption("SIDER: configured on server" if sider_path else "SIDER: not configured on this server; it will be recorded as skipped.")
            ai = st.checkbox("Add Gemini synthesis (public evidence sent to Google)", value=False, disabled=not allow_gemini)
            if not allow_gemini:
                st.caption("AI is disabled on this deployment. Statistics and template reports remain available.")
            confirmed = st.checkbox("I confirm the ingredient and understand this is exploratory report analysis.")
            analyze = st.form_submit_button("Run analysis")
        if analyze:
            st.session_state.pop("analysis_result", None)
            cooldown = max(0, 30 - (time.monotonic() - st.session_state.get("last_analysis_at", -1000)))
            if not confirmed:
                st.warning("Confirm the ingredient and analysis scope first.")
            elif start > end:
                st.error("Start year must not exceed end year.")
            elif cooldown:
                st.warning(f"Please wait {int(cooldown) + 1} seconds before another request.")
            else:
                st.session_state["last_analysis_at"] = time.monotonic()
                progress = st.empty()
                try:
                    if ai:
                        get_gemini_model()
                    with st.spinner("Retrieving public evidence and calculating results..."):
                        with tempfile.TemporaryDirectory(prefix="openpulse_") as temporary:
                            result = run_analysis(ingredient, event_key, int(start), int(end), drug_selection=identity,
                                                  include_trials=trials, include_approval=approval, sider_directory=sider_path or None,
                                                  use_gemini=ai, progress=progress.info, output_root=temporary)
                            st.session_state["analysis_result"] = {
                                "report": result["report"], "zip_bytes": result["bundle"].read_bytes(),
                                "table": result["table"], "statistics": result["statistics"], "sources": result["sources"],
                                "definition": f"{ingredient} · {catalog['events'][event_key]['faers_term']} · {start}–{end}",
                            }
                    progress.success("Core analysis completed. Review warnings and source statuses.")
                except Exception as exc:
                    progress.empty()
                    st.error(f"Analysis did not complete: {exc}. No previous result is presented as a new result.")
    result = st.session_state.get("analysis_result")
    if result:
        st.subheader("Results")
        st.caption("Submitted analysis: " + result["definition"] + ". Changing the form does not rerun the analysis.")
        for column, metric in zip(st.columns(2), ("PRR", "ROR")):
            value = result["statistics"][metric]
            column.metric(metric, format_stat(value["estimate"]))
            column.caption(f"95% CI: {format_stat(value['ci_lower'])}–{format_stat(value['ci_upper'])}")
        for warning in result["statistics"].get("warnings", []):
            st.caption(warning)
        table = result["table"]
        st.table([{"Drug matching": "Matched", "Event matched": table["a"], "Event not matched": table["b"]},
                  {"Drug matching": "Not matched", "Event matched": table["c"], "Event not matched": table["d"]}])
        st.table([{"Source": name, "Status": status} for name, status in result["sources"].items()])
        st.download_button("Download analysis ZIP", result["zip_bytes"], file_name="openpulse_analysis.zip", mime="application/zip")
        st.download_button("Download report", result["report"], file_name="report.md", mime="text/markdown")
        with st.expander("Read report", expanded=True):
            st.markdown(result["report"])
