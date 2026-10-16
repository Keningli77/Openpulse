"""Discover DailyMed products and resolve ingredients from authoritative SPL text."""

import hashlib
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://dailymed.nlm.nih.gov/dailymed/"
NS = {"s": "urn:hl7-org:v3"}


def fetch_bytes(url, max_bytes=64 * 1024 * 1024):
    request = Request(url, headers={"User-Agent": "OpenPulse-MVP/1.0"})
    with urlopen(request, timeout=45) as response:
        if not response.geturl().startswith("https://"):
            raise ValueError("Expected an HTTPS data source")
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("Response exceeds the configured size limit")
        return data


def search_labels(name, page=1):
    name = name.strip()
    if not 2 <= len(name) <= 100 or page < 1:
        raise ValueError("Enter a drug name of 2–100 characters and a positive page")
    url = BASE + "services/v2/spls.json?" + urlencode({"drug_name": name, "page": page, "pagesize": 20})
    payload = json.loads(fetch_bytes(url, 4 * 1024 * 1024))
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("Unexpected DailyMed search response")
    candidates = [item for item in payload["data"] if item.get("setid") and item.get("title")]
    return {"candidates": candidates, "metadata": payload.get("metadata", {}), "source_url": url, "query": name}


def parse_identity(xml, setid):
    root = ET.fromstring(xml)
    if root.tag != "{urn:hl7-org:v3}document":
        raise ValueError("Not a structured SPL document")
    actual = root.find("s:setId", NS)
    if actual is None or str(actual.get("root", "")).casefold() != setid.casefold():
        raise ValueError("Downloaded label SETID mismatch")
    substances, query_terms = set(), set()
    for ingredient in root.findall(".//s:ingredient", NS):
        if ingredient.get("classCode") not in {"ACTIB", "ACTIM", "ACTIR"}:
            continue
        node = ingredient.find("s:ingredientSubstance", NS)
        if node is None:
            continue
        names = {" ".join(item.itertext()).strip().lower() for item in node.findall("s:name", NS)} - {""}
        substances.update(names)
        moieties = {" ".join(item.itertext()).strip().lower() for item in node.findall(".//s:activeMoiety/s:name", NS)} - {""}
        query_terms.update(moieties or names)
    title_node = root.find("s:title", NS)
    title = " ".join(title_node.itertext()).strip() if title_node is not None else ""
    if not title or not substances or not query_terms:
        raise ValueError("Could not resolve a product title and active ingredients; manual review required")
    version = root.find("s:versionNumber", NS)
    return {
        "label_setid": setid, "reference_product": title,
        "reference_ingredients": sorted(substances), "query_ingredients": sorted(query_terms),
        "reference_version": version.get("value") if version is not None else None,
        "mapping_source": BASE + "drugInfo.cfm?" + urlencode({"setid": setid}),
        "mapping_evidence": "SPL active ingredientSubstance; activeMoiety used as the query ingredient when provided",
        "xml_sha256_at_selection": hashlib.sha256(xml).hexdigest(),
        "faers_scope": "Ingredient-level standardized generic-name phrase matching, including single and combination products. The selected product label is contextual evidence, not an exhaustive product dictionary.",
    }


def resolve_label(setid):
    if not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", setid):
        raise ValueError("Invalid label SETID")
    raw = fetch_bytes(BASE + "downloadzipfile.cfm?" + urlencode({"setId": setid}))
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        xmls = [item for item in archive.infolist() if item.filename.lower().endswith(".xml")]
        if len(xmls) != 1 or xmls[0].file_size > 32 * 1024 * 1024:
            raise ValueError("Unexpected SPL ZIP contents")
        xml = archive.read(xmls[0])
    return parse_identity(xml, setid)
