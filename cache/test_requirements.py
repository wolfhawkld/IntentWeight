#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for requirements.txt dependency declarations.

Run from repo root:
    .venv/bin/python cache/test_requirements.py
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO_ROOT / "requirements.txt"


class RequirementsTests(unittest.TestCase):
    def test_requirements_include_runtime_and_experiment_dependencies(self):
        content = REQUIREMENTS.read_text(encoding="utf-8")
        required = {
            "loguru": "0.7.0",
            "rank-bm25": "0.2.2",
            "faiss-cpu": "1.8.0",
            "hnswlib": "0.8.0",
            "ragas": "0.2.0",
        }
        for package, min_version in required.items():
            pattern = rf"(?m)^\s*{re.escape(package)}\s*>=\s*{re.escape(min_version)}\s*$"
            self.assertRegex(content, pattern, f"missing requirement: {package}>={min_version}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
