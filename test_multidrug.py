"""Synthetic search/identity/workflow/UI tests. Not a claim of live clinical validation."""

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import drug_search
import workflow
from faers_stats import compute_statistics

SID = "11111111-2222-3333-4444-555555555555"


def product_xml(ingredient="dapagliflozin propanediol", moiety="dapagliflozin", title="FARXIGA"):
    return f'''<document xmlns="urn:hl7-org:v3"><title>{title}</title>
    <setId root="{SID}"/><versionNumber value="1"/><effectiveTime value="20260101"/>
    <ingredient classCode="ACTIB"><ingredientSubstance><name>{ingredient}</name>
    <activeMoiety><activeMoiety><name>{moiety}</name></activeMoiety></activeMoiety>
    </ingredientSubstance></ingredient>
    <ingredient classCode="IACT"><ingredientSubstance><name>INACTIVE EXAMPLE</name></ingredientSubstance></ingredient>
    <component><structuredBody><component><section><title>Warnings</title>
    <text>Synthetic urinary tract infection text; not actual product evidence.</text>
    </section></component></structuredBody></component></document>'''.encode()


def product_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("product.xml", product_xml())
    return buffer.getvalue()


class MultiDrugTests(unittest.TestCase):
    def test_ingredient_and_moiety_resolution(self):
        resolved = drug_search.parse_identity(product_xml(), SID)
        self.assertEqual(resolved["reference_ingredients"], ["dapagliflozin propanediol"])
        self.assertEqual(resolved["query_ingredients"], ["dapagliflozin"])
        with self.assertRaisesRegex(ValueError, "SETID"):
            drug_search.parse_identity(product_xml(), "different")

    def test_missing_active_identity_not_guessed(self):
        with self.assertRaises(ValueError):
            drug_search.parse_identity(f'<document xmlns="urn:hl7-org:v3"><setId root="{SID}"/><title>Unknown</title></document>'.encode(), SID)

    def test_search_encodes_name_and_page(self):
        payload = {"data": [{"setid": SID, "title": "FARXIGA"}], "metadata": {"current_page": 2}}
        with patch.object(drug_search, "fetch_bytes", return_value=json.dumps(payload).encode()) as request:
            result = drug_search.search_labels("farxiga", 2)
        self.assertIn("drug_name=farxiga&page=2", request.call_args.args[0])
        self.assertEqual(len(result["candidates"]), 1)

    def test_new_ingredient_workflow_and_zero_cells(self):
        selection = drug_search.parse_identity(product_xml(), SID)
        for totals, expected_prr in (([10000, 1000, 400, 80], 2.25), ([10000, 0, 400, 0], None)):
            values = iter(totals)
            with tempfile.TemporaryDirectory() as directory, \
                 patch.object(workflow, "fetch_total", side_effect=lambda query: {"total": next(values), "url": "synthetic", "response": {}}), \
                 patch.object(workflow, "get_bytes", return_value=product_zip()):
                result = workflow.run_analysis("dapagliflozin", "uti", 2022, 2024,
                    drug_selection=selection, include_trials=False, include_approval=False, output_root=directory)
                if expected_prr is None:
                    self.assertIsNone(result["statistics"]["PRR"]["estimate"])
                    self.assertIn("Not estimable", result["report"])
                else:
                    self.assertAlmostEqual(result["statistics"]["PRR"]["estimate"], expected_prr)
                self.assertIn("dapagliflozin", result["report"])
                definition = json.loads((result["folder"] / "audit.json").read_text())["definition"]
                self.assertEqual(definition["reference_label_setid"], SID)
                with zipfile.ZipFile(result["bundle"]) as archive:
                    self.assertIsNone(archive.testzip())

    def test_selection_cannot_be_used_for_another_ingredient(self):
        selection = drug_search.parse_identity(product_xml(), SID)
        with self.assertRaisesRegex(ValueError, "query ingredient"):
            workflow.run_analysis("unrelated", "uti", 2022, 2024, drug_selection=selection)

    def test_zero_events_not_reported_as_no_risk(self):
        result = compute_statistics({"a": 0, "b": 100, "c": 5, "d": 895})
        self.assertEqual(result["PRR"]["estimate"], 0)
        self.assertIsNone(result["PRR"]["ci_lower"])
        self.assertIsNone(result["continuity_correction"])

    def test_reference_statistics_unchanged(self):
        result = compute_statistics({"a": 974, "b": 27280, "c": 2878, "d": 4180210})
        self.assertAlmostEqual(result["PRR"]["estimate"], 50.1055, places=4)
        self.assertAlmostEqual(result["ROR"]["estimate"], 51.8587, places=4)


class WebTests(unittest.TestCase):
    def test_search_to_zip_and_new_search_clears_results(self):
        from streamlit.testing.v1 import AppTest
        found = {"query": "dapagliflozin", "candidates": [{"setid": SID, "title": "FARXIGA"}], "metadata": {}}
        selection = drug_search.parse_identity(product_xml(), SID)
        values = iter([10000, 1000, 400, 80])
        with patch.object(drug_search, "search_labels", return_value=found), \
             patch.object(drug_search, "resolve_label", return_value=selection), \
             patch.object(workflow, "fetch_total", side_effect=lambda query: {"total": next(values), "url": "synthetic", "response": {}}), \
             patch.object(workflow, "get_bytes", return_value=product_zip()), \
             patch.object(workflow, "get_trial_population", return_value={"status": "completed", "population_context": []}), \
             patch.object(workflow, "get_approval_metadata", return_value={"status": "completed", "response": {"results": []}}):
            app = AppTest.from_file(str(Path(__file__).with_name("app.py"))).run()
            self.assertFalse(app.exception)
            app.text_input[0].set_value("dapagliflozin")
            next(button for button in app.button if button.label == "Search products").click().run()
            next(button for button in app.button if button.label == "Read label ingredients").click().run()
            next(item for item in app.selectbox if item.label == "Event (single defined term)").select("uti")
            next(item for item in app.checkbox if item.label.startswith("I confirm")).check()
            next(button for button in app.button if button.label == "Run analysis").click().run(timeout=30)
            self.assertFalse(app.exception)
            self.assertEqual(app.metric[0].value, "2.2500")
            result = app.session_state["analysis_result"]
            with zipfile.ZipFile(io.BytesIO(result["zip_bytes"])) as archive:
                self.assertIn("drug_selection.json", archive.namelist())
            next(button for button in app.button if button.label == "Search products").click().run()
            self.assertEqual(len(app.metric), 0)


if __name__ == "__main__":
    unittest.main()
