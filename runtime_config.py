"""Single backend source for the Gemini model; credentials remain in the environment."""

import json
import re
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().with_name("backend_settings.json")


def get_gemini_model():
    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Cannot read backend_settings.json. Check that the file exists and contains valid JSON.") from exc
    if not isinstance(settings, dict) or settings.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported backend settings schema")
    gemini = settings.get("gemini")
    model = gemini.get("model") if isinstance(gemini, dict) else None
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", model):
        raise ValueError("Set a valid Gemini model identifier in backend_settings.json")
    return model
