# Publish an OpenPulse demo

## Streamlit Community Cloud

1. Sign in at https://share.streamlit.io/ with the GitHub account that can access the repository.
2. Create an app from the repository, choose the branch containing this release, and set the main file to `app.py`.
3. In advanced settings, select Python 3.12. Leave Gemini disabled for the first launch.
4. Deploy. The platform will provide the actual public `*.streamlit.app` URL. No public URL exists merely from running a local terminal command.
5. Open the generated URL in a private browser window or on your phone. Check the saved example and a live search, resolve ingredients, submit, and download a ZIP.
6. Share the actual published URL only after that external check succeeds. Later commits to the same app branch normally update the same URL.

No actual deployment credentials or keys are stored in the repository. The AI assistant cannot sign in to your hosting account for you. The deployment owner completes account authorization and the final platform action.

## Optional Gemini

In the platform's Secrets editor (not GitHub source), set your actual key securely and enable synthesis:

```toml
ENABLE_GEMINI = "true"
GEMINI_API_KEY = "YOUR_PRIVATE_VALUE"
```

The value above is a placeholder, not a usable key. The model is configured in `backend_settings.json`, using the model identifier previously recommended by the user's API response; availability still depends on your account. Turning on AI allows explicitly requested public evidence excerpts to be sent to Google and may incur charges. Public users do not enter keys or model names. To disable synthesis, set `ENABLE_GEMINI = "false"`.

## Optional SIDER

The deployment does not include the user's laptop dataset. Without a server-side dataset, the UI and report clearly show SIDER as skipped.

To configure it later, prepare the source files on the server through the supported deployment workflow, verify their provenance and release, and set `SIDER_DATA_DIR` to the server directory containing:

- `drug_names.tsv`
- `meddra_all_se.tsv.gz`
- `manifest.json`

Do not point a server to a laptop path. Do not label unversioned downloads as a verified release. Review SIDER data-use conditions before redistributing files. The current app does not fetch that dataset automatically at startup.

## Troubleshooting

- Empty page: verify `app.py` contains code, and inspect deployment logs.
- Import failure: check all Python modules are included at the repository root and `requirements.txt` is installed.
- Search fails: the server must reach `dailymed.nlm.nih.gov`; analysis also needs `api.fda.gov`. The saved example remains available.
- Trials unavailable: check access to `clinicaltrials.gov`. Auxiliary failure does not become a zero-risk statement.
- Gemini failure: review sanitized error fields in downloaded `gemini.json`; do not publish a key or raw authenticated request.
- Undefined result: zero event/drug counts are valid lookup outcomes, not evidence of safety. The app does not manufacture a confidence interval.

The hosted instance may sleep or restart. This prototype has no uptime guarantee, user accounts, or persistent analysis database. No local loopback address can be submitted as the public application URL.
