# Web quick start

The current application searches DailyMed products and confirms ingredients before analysis.
For current local instructions, scope, and limitations, see [README.md](README.md).
For the public URL deployment steps, see [DEPLOY.md](DEPLOY.md).

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

No API key is required for the template workflow. Gemini is an explicit administrator opt-in;
its model is defined only in backend_settings.json. SIDER must be present on the server,
otherwise the app records it as skipped.
