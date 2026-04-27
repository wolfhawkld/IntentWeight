#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for paper/experiments/scripts/download_parquet.py.

Run from repo root:
    python cache/test_download_parquet.py
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "download_parquet.py"


def load_module():
    spec = importlib.util.spec_from_file_location("download_parquet", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DownloadParquetTests(unittest.TestCase):
    def test_download_file_uses_resume_and_fail_fast_flags(self):
        module = load_module()
        calls = []

        class Result:
            returncode = 0
            stderr = ""

        def fake_run(cmd, capture_output=True, text=True):
            calls.append(cmd)
            return Result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "dataset.parquet"
            output_path.write_bytes(b"PAR1 fake")
            with patch.object(module.subprocess, "run", side_effect=fake_run):
                ok = module.download_file("https://example.com/data.parquet", str(output_path), proxy="http://proxy:7897")

        self.assertTrue(ok)
        self.assertEqual(len(calls), 1)
        cmd = calls[0]
        self.assertIn("curl", cmd)
        self.assertIn("-L", cmd)
        self.assertIn("-C", cmd)
        self.assertIn("-", cmd)
        self.assertIn("-f", cmd)
        self.assertIn("-o", cmd)
        self.assertIn("-x", cmd)
        self.assertIn("http://proxy:7897", cmd)

    def test_main_redownloads_existing_file_when_verification_fails(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir)
            broken = raw_dir / "broken.parquet"
            broken.write_bytes(b"not a valid parquet but larger than 1KB" * 50)

            downloads = []

            def fake_download(url, output_path, proxy=None):
                downloads.append((url, output_path, proxy))
                Path(output_path).write_bytes(b"PAR1 repaired")
                return True

            # First verification is for the existing broken file -> False.
            # Second verification is after download -> True.
            verify_results = iter([False, True])

            with patch.object(module, "RAW_DIR", str(raw_dir)), \
                 patch.object(module, "PARQUET_URLS", {"broken": {"url": "https://example.com/broken.parquet", "filename": "broken.parquet"}}), \
                 patch.object(module, "verify_parquet", side_effect=lambda path: next(verify_results)), \
                 patch.object(module, "download_file", side_effect=fake_download):
                module.main()

        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0][0], "https://example.com/broken.parquet")


if __name__ == "__main__":
    unittest.main(verbosity=2)
