"""Regression checks for data that previously passed CI but broke rendering."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_site


class SiteValidationTests(unittest.TestCase):
    def test_curated_datasets_satisfy_contracts(self):
        for path in validate_site.DATA.glob("*.json"):
            with self.subTest(filename=path.name):
                self.assertEqual(validate_site.validate_data(path.name, json.loads(path.read_text(encoding="utf-8"))), [])

    def test_missing_datasets_fail(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(validate_site, "DATA", Path(directory)):
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(validate_site.main(), 1)
            for filename in validate_site.REQUIRED_FILES:
                self.assertIn(filename, errors.getvalue())

    def test_wrong_root_types_fail(self):
        for filename in validate_site.REQUIRED_FILES:
            invalid = {} if filename in validate_site.COLLECTION_FIELDS else []
            with self.subTest(filename=filename):
                self.assertTrue(validate_site.validate_data(filename, invalid))

    def test_malformed_records_and_nested_arrays_fail(self):
        cases = (
            ("research.json", [None]),
            ("research.json", [{}]),
            ("experience.json", [{"period": "2026", "role": "Engineer", "organization": "Example", "description": "Work", "tags": "Python"}]),
            ("skills.json", [{"name": "Languages", "items": [None]}]),
            ("projects.json", [{"title": "Project", "description": "Work", "category": "unrendered-category"}]),
            ("publications.json", [{"title": "Paper", "links": {}}]),
            ("research.json", [{"title": "Project", "url": "javascript:alert(1)"}]),
        )
        for filename, value in cases:
            with self.subTest(filename=filename, value=value):
                self.assertTrue(validate_site.validate_data(filename, value))

    def test_sync_requires_query_and_positive_limit(self):
        config = {"username": "contributor", "approvedRepositories": ["owner/project"], "maxContributions": 0}
        errors = "\n".join(validate_site.validate_data("github-sync.json", config))
        self.assertIn(".query", errors)
        self.assertIn(".maxContributions", errors)

    def test_zero_is_valid_but_boolean_is_not_a_count(self):
        snapshot = {"generatedAt": "2026-11-15T00:00:00Z", "metrics": {"mergedPrs": 0}, "contributions": []}
        self.assertEqual(validate_site.validate_data("github.json", snapshot), [])
        snapshot["metrics"]["mergedPrs"] = False
        self.assertTrue(validate_site.validate_data("github.json", snapshot))

    def test_research_without_a_public_link_is_valid(self):
        self.assertEqual(validate_site.validate_data("research.json", [{"title": "Work in progress"}]), [])

    def test_timestamp_requires_timezone(self):
        snapshot = {"generatedAt": "2026-11-15T00:00:00", "metrics": {"mergedPrs": 0}, "contributions": []}
        self.assertTrue(validate_site.validate_data("github.json", snapshot))


if __name__ == "__main__":
    unittest.main()
