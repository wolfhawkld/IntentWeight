import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper" / "experiments" / "scripts" / "task74_validate_task73_integration.py"
SPEC = importlib.util.spec_from_file_location("task74_validate_task73_integration", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Task74IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(MODULE.SOURCE.read_text(encoding="utf-8"))

    def test_expected_table_covers_both_domains_and_controls(self):
        rows = MODULE.expected_s30(self.payload)
        self.assertEqual(4, len(rows))
        self.assertEqual(
            [
                "recreation / trust",
                "recreation / no feedback",
                "writing / trust",
                "writing / no feedback",
            ],
            [row[0] for row in rows],
        )

    def test_dense_fallback_is_not_reported_as_strict_ni(self):
        rows = MODULE.expected_s30(self.payload)
        self.assertEqual("n/a (fallback)", rows[0][-1])
        self.assertEqual("n/a (fallback)", rows[2][-1])

    def test_source_derived_budget_values(self):
        rows = MODULE.expected_s30(self.payload)
        self.assertEqual(["4/5", "-0.76 pp", "5.42%", "0/3"], rows[1][5:])
        self.assertEqual(["5/5", "+0.12 pp", "10.09%", "2/3"], rows[3][5:])

    def test_markdown_table_matches_source(self):
        self.assertEqual(MODULE.expected_s30(self.payload), MODULE.parse_supplementary_table(30))


if __name__ == "__main__":
    unittest.main()
