# OpenPulse

A Streamlit research MVP for exploratory FAERS reporting disproportionality, drug-label cross-checks, and reproducible evidence reports.

Search a drug by generic or brand name, select a DailyMed product label, resolve its active ingredients from structured label XML, confirm an ingredient, and run an analysis. Export Markdown, a versioned analysis definition, source responses, and provenance in a ZIP.

## Run locally

Python 3.12 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The **Saved example** tab contains a previously generated empagliflozin–DKA report. It is explicitly a historical example, not a live result or validation benchmark.

## Live workflow

1. Enter a generic or brand name, for example `empagliflozin`, `dapagliflozin`, or `canagliflozin`.
2. Select the intended product from DailyMed search results.
3. Click **Read label ingredients**. Ingredients and active moieties come from SPL XML, not fuzzy name inference.
4. Choose one resolved ingredient and one defined event, confirm scope, and run.
5. Review counts, statistics, source statuses, limitations, and download the analysis package.

The current event definitions are single PT queries: `Diabetic ketoacidosis`, `Urinary tract infection`, and `Lower limb amputation`. They are not complete clinical synonym groups. A search match alone is not methodological validation.

## Deploy

See [DEPLOY.md](DEPLOY.md) for Streamlit Community Cloud. Entry point: `app.py`. No credentials are required for the default template report. Public deployment defaults to Gemini disabled; the saved example requires no external service.

Optional admin configuration uses environment variables or Streamlit Secrets:

- `ENABLE_GEMINI = "true"` and `GEMINI_API_KEY` enable opt-in AI synthesis. The model is read only from `backend_settings.json`.
- `SIDER_DATA_DIR` points to a server-side directory containing the two source files and manifest. If absent, SIDER is explicitly skipped. Local laptop data does not automatically appear on the server.

Do not commit API keys, actual `.streamlit/secrets.toml`, `.env`, local datasets, or exported runs. Model costs and quotas remain the deployment owner's responsibility; the session cooldown is not a global budget limit.

## Analysis and boundaries

- FAERS uses `receivedate` (first receipt), current latest report versions, ingredient generic-name phrase matching, and an all-other-reports comparator in the same period. Both single and combination products can enter. No suspect-role filter or cross-report case deduplication is applied.
- PRR/ROR are reporting metrics, **not incidence, patient risk ratios, or causal effects**. Independent-count log-Wald intervals are used without automatic 0.5 correction. Zero cells produce an explicit unavailable interval, not a claim of no risk.
- The reference label is rechecked for SETID, title and active ingredient substances. Its current content does not establish labeling during earlier years. Label identity does not prove full FAERS name coverage.
- Trial and approval adapters return a limited first page. Trial eligibility is not an observed enrollment description. SIDER non-matches are dataset-specific; the downloaded release remains unverified unless independently established.
- Gemini is an optional synthesis appendix with narrow error checks and human review flags, **not autonomous function calling** and not a substitute for statistical or clinical validation.
- Temporary live analysis files are deleted after the session result is assembled in memory. Download before leaving the session; no durable analysis-history service is provided.

## Tests and evidence

```bash
python -m unittest test_workflow test_multidrug -v
```

Thirteen tests cover synthetic identity/moiety resolution, a second drug workflow, the original reference statistics, zero cells, core/optional failures, SIDER lookup states, and Streamlit search-to-download behavior. Prior user-run empagliflozin–DKA analysis verified the baseline public APIs locally. New drug searches still need live validation in the deployed runtime; cloud egress prevented live FDA/DailyMed checks during this change.

The repository is a deployable prototype, not a fully validated pharmacovigilance study. Full matching sensitivity, independent count validation, historical labeling, SIDER release verification, and additional real-case validation remain open work.
