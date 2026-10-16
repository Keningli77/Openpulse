"""Inspect a small FAERS API sample; not a PRR/ROR analysis."""

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drug", default="empagliflozin")
    parser.add_argument("--output", type=Path, default=Path("data/faers_sample.json"))
    parser.add_argument("--input", type=Path, help="Inspect previously saved API JSON offline")
    args = parser.parse_args()

    if args.input:
        try:
            payload = json.loads(args.input.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"Cannot read input: {exc}", file=sys.stderr)
            return 1
    else:
        drug = args.drug.strip()
        if not drug or any(char in drug for char in ('"', '\\')):
            parser.error("Provide a nonempty drug name without quotes or backslashes")
        query = f'patient.drug.openfda.generic_name:"{drug}"'
        url = "https://api.fda.gov/drug/event.json?" + urlencode(
            {"search": query, "limit": 1}
        )
        print(f"Request: {url}")
        if args.output.exists():
            print("Output already exists; choose another --output or use --input.", file=sys.stderr)
            return 1
        try:
            with urlopen(url, timeout=30) as response:
                payload = json.load(response)
        except HTTPError as exc:
            print(f"API HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
            return 1
        except (URLError, TimeoutError, ValueError) as exc:
            print(f"Request failed: {exc}", file=sys.stderr)
            return 1
        if not isinstance(payload, dict) or not payload.get("results"):
            print("No report returned; no sample saved.", file=sys.stderr)
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        print(f"Saved: {args.output}")

    if not isinstance(payload, dict) or not payload.get("results"):
        print("Input does not contain FAERS reports.", file=sys.stderr)
        return 1
    for report in payload["results"]:
        patient = report.get("patient", {})
        print(f"\nReport ID: {report.get('safetyreportid', 'missing')}")
        print(f"Version: {report.get('safetyreportversion', 'missing')}")
        print("Drugs:")
        for drug in patient.get("drug", []):
            print(" -", drug.get("medicinalproduct", "missing"),
                  "| generic:", drug.get("openfda", {}).get("generic_name", []))
        print("Events:")
        for reaction in patient.get("reaction", []):
            print(" -", reaction.get("reactionmeddrapt", "missing"))
    print("\nSample inspection only. This query does not establish complete drug coverage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
