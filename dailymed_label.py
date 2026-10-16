"""List DailyMed labels or inspect a manually selected SPL label."""

import argparse
import io
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = "https://dailymed.nlm.nih.gov/dailymed/"
NS = {"s": "urn:hl7-org:v3"}


def get_bytes(url):
    with urlopen(url, timeout=45) as response:
        return response.read()


def extract_sections(xml, keyword):
    root = ET.fromstring(xml)
    if root.tag != "{urn:hl7-org:v3}document":
        raise ValueError("Downloaded content is not an HL7 SPL label document")
    hits = []
    for section in root.findall(".//s:section", NS):
        title = section.find("s:title", NS)
        title_text = " ".join(title.itertext()).strip() if title is not None else "Untitled section"
        narratives = section.findall("s:text", NS)
        text = "\n".join(" ".join(item.itertext()) for item in narratives)
        text = re.sub(r"[ \t]+", " ", text).strip()
        if keyword.casefold() in text.casefold() or keyword.casefold() in title_text.casefold():
            hits.append({"section_title": title_text, "text": text})
    def attr(path, name):
        element = root.find(path, NS)
        return element.get(name) if element is not None else None
    return {
        "document_id": attr("s:id", "root"),
        "setid": attr("s:setId", "root"),
        "version": attr("s:versionNumber", "value"),
        "effective_time": attr("s:effectiveTime", "value"),
        "matches": hits,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drug", default="empagliflozin")
    parser.add_argument("--setid", help="Label SETID from search results; omit to list candidates")
    parser.add_argument("--keyword", default="ketoacidosis")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    if not args.drug.strip() or not args.keyword.strip() or args.page < 1:
        parser.error("Drug and keyword must not be empty; page must be at least 1")
    if args.setid and not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", args.setid):
        parser.error("SETID must be a UUID from the label list, not a drug name")
    now = datetime.now(timezone.utc)
    folder = args.output_dir / ("label_" + now.strftime("%Y%m%dT%H%M%S%fZ"))
    record = {
        "status": "running", "retrieved_at_utc": now.isoformat(),
        "drug_input": args.drug.strip(), "keyword": args.keyword.strip(),
        "limitations": [
            "Verify ingredients, dosage form, product, and date before selecting a label. Results may include combination products.",
            "Keyword matches do not establish causality. No match does not mean the risk is absent.",
            "Current labeling does not establish historical labeling during the FAERS years. Historical versions are not retrieved.",
            "Extracted XML text does not preserve full table formatting. Check the original label.",
        ],
    }
    try:
        folder.mkdir(parents=True, exist_ok=False)
        if not args.setid:
            url = BASE + "services/v2/spls.json?" + urlencode({"drug_name": args.drug.strip(), "page": args.page, "pagesize": 20})
            record["source_url"] = url
            raw = get_bytes(url)
            (folder / "search.json").write_bytes(raw)
            payload = json.loads(raw)
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                raise ValueError("Unexpected label search response structure")
            record.update(status="candidates_only", candidates=payload["data"], pagination=payload.get("metadata"))
            print("Candidate labels (verify the product before selecting SETID; full text not yet retrieved):")
            for label in payload["data"]:
                print(f"\nTitle: {label.get('title')}\nSETID: {label.get('setid')}\nPublished: {label.get('published_date')}")
            print("\nPagination:", payload.get("metadata"))
            if not payload["data"]:
                print("No candidates on this page; this does not establish that no label exists.")
        else:
            setid = args.setid.lower()
            # DailyMed's public label-download route supplies the complete SPL ZIP.
            url = BASE + "downloadzipfile.cfm?" + urlencode({"setId": setid})
            record.update(source_url=url, label_url=BASE + "drugInfo.cfm?" + urlencode({"setid": setid}))
            raw = get_bytes(url)
            (folder / "label.zip").write_bytes(raw)
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                xml_files = [info for info in archive.infolist() if info.filename.lower().endswith(".xml")]
                if len(xml_files) != 1:
                    raise ValueError("Expected exactly one XML file in the ZIP")
                if xml_files[0].file_size > 32 * 1024 * 1024:
                    raise ValueError("Label XML exceeds the size limit")
                xml = archive.read(xml_files[0])
            (folder / "label.xml").write_bytes(xml)
            parsed = extract_sections(xml, args.keyword.strip())
            if not parsed["setid"] or parsed["setid"].lower() != setid:
                raise ValueError("Downloaded SETID does not match the requested label")
            record.update(status="completed", label=parsed)
            print(f"Label SETID: {parsed['setid']}\nVersion: {parsed['version']}\nEffective time: {parsed['effective_time']}")
            print("Original label:", record["label_url"])
            for hit in parsed["matches"]:
                print(f"\nSECTION: {hit['section_title']}\n{hit['text']}\n")
            print(f"Found {len(parsed['matches'])} matching sections. Extracted text is saved in the results.")
            if not parsed["matches"]:
                print("Keyword not found. Review the label and alternative terms; do not conclude the risk is absent.")
    except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile) as exc:
        record.update(status="failed", error=str(exc))
        print(f"Failed:{exc}", file=sys.stderr)
    try:
        with (folder / "label_result.json").open("x", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
    except OSError as exc:
        print(f"Could not save:{exc}", file=sys.stderr)
        return 1
    print("Saved to:", folder)
    return 1 if record["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
