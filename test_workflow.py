"""Synthetic integration tests; never claimed as live FDA validation."""

import gzip
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import workflow
from evidence_sources import get_sider_side_effects


def label_zip(ingredient="EMPAGLIFLOZIN"):
    xml = f'''<document xmlns="urn:hl7-org:v3"><title>JARDIANCE</title>
    <setId root="faf3dd6a-9cd0-39c2-0d2e-232cb3f67565"/><versionNumber value="31"/>
    <effectiveTime value="20260130"/><ingredient classCode="ACTIB"><ingredientSubstance>
    <name>{ingredient}</name></ingredientSubstance></ingredient>
    <component><structuredBody><component><section><title>Warnings</title>
    <text>Synthetic ketoacidosis evidence, not actual label text.</text>
    </section></component></structuredBody></component></document>'''
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("label.xml", xml)
    return buffer.getvalue()


class WorkflowTests(unittest.TestCase):
    def test_end_to_end_with_failed_optional_source(self):
        values = iter([10000, 1000, 280, 100])
        def fetch(query):
            return {"total": next(values), "url": "synthetic", "response": {}}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(workflow, "fetch_total", side_effect=fetch), \
             patch.object(workflow, "get_bytes", return_value=label_zip()), \
             patch.object(workflow, "get_trial_population", side_effect=OSError("synthetic network error")):
            result = workflow.run_analysis("empagliflozin", "dka", 2022, 2024,
                                           include_approval=False, output_root=directory)
            self.assertAlmostEqual(result["statistics"]["PRR"]["estimate"], 5)
            self.assertEqual(result["sources"]["clinical_trials"], "failed")
            self.assertEqual(result["sources"]["sider"], "skipped")
            self.assertIn("synthetic network error", result["report"])
            self.assertEqual(json.loads((result["folder"] / "run.json").read_text())["status"], "completed")
            with zipfile.ZipFile(result["bundle"]) as archive:
                self.assertTrue({"report.md", "cohort.yaml", "label.xml", "audit.json", "provenance.json"} <= set(archive.namelist()))

    def test_wrong_ingredient_stops_report(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(workflow, "get_bytes", return_value=label_zip("OTHER")):
            catalog = workflow.read_catalog()
            with self.assertRaisesRegex(ValueError, "active ingredients"):
                workflow.fetch_verified_label(catalog["drugs"]["empagliflozin"], catalog["events"]["dka"], Path(directory))

    def test_core_failure_does_not_create_report(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(workflow, "fetch_total", side_effect=OSError("blocked")):
            with self.assertRaises(RuntimeError):
                workflow.run_analysis("empagliflozin", "dka", 2022, 2024, output_root=directory)
            folder = next(Path(directory).iterdir())
            self.assertFalse((folder / "report.md").exists())
            self.assertEqual(json.loads((folder / "run.json").read_text())["status"], "failed")

    def test_unsupported_input(self):
        with self.assertRaisesRegex(ValueError, "Search and confirm"):
            workflow.run_analysis("unknown", "dka", 2022, 2024)

    def test_sider_match_and_unmatched_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps({"version": "synthetic", "source_url": "synthetic"}))
            (root / "drug_names.tsv").write_text("CID1\tempagliflozin\n")
            with gzip.open(root / "meddra_all_se.tsv.gz", "wt") as handle:
                handle.write("CID1\tCID2\tC0\tPT\tC1\tDiabetic ketoacidosis\n")
            result = get_sider_side_effects("empagliflozin", ["Diabetic ketoacidosis"], root)
            self.assertEqual(len(result["matches"]), 1)
            self.assertEqual(get_sider_side_effects("unknown", ["Diabetic ketoacidosis"], root)["drug_match_status"], "unmatched")


if __name__ == "__main__":
    unittest.main()
