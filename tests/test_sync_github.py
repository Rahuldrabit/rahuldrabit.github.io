"""Regression checks for publishing complete, stable GitHub snapshots."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from scripts import sync_github


class GithubSyncTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.output = self.directory / "github.json"
        self.config = self.directory / "config.json"
        self.config.write_text(json.dumps({
            "query": "author:contributor is:pr",
            "approvedRepositories": ["owner/project"],
            "maxContributions": 12,
        }), encoding="utf-8")
        for patcher in (
            patch.dict(os.environ, {"GITHUB_TOKEN": "test-placeholder"}),
            patch.object(sync_github, "CONFIG_PATH", self.config),
            patch.object(sync_github, "OUTPUT_PATH", self.output),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def item(self, number):
        return {
            "number": number,
            "repository_url": "https://api.github.com/repos/owner/project",
            "url": f"https://api.github.com/repos/owner/project/issues/{number}",
            "pull_request": {"url": f"https://api.github.com/repos/owner/project/pulls/{number}"},
        }

    def detail(self, number, merged=True, body="Description"):
        return {
            "number": number, "title": f"Contribution {number}", "body": body,
            "state": "closed" if merged else "open",
            "merged_at": "2026-10-02T10:00:00Z" if merged else None,
            "updated_at": "2026-10-03T11:00:00Z",
            "html_url": f"https://github.com/owner/project/pull/{number}",
        }

    def run_sync(self, request):
        with patch.object(sync_github, "request_json", side_effect=request), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sync_github.main(), 0)
        return json.loads(self.output.read_text(encoding="utf-8"))

    def test_uses_pr_details_and_handles_null_description(self):
        urls = []

        def request(url):
            urls.append(url)
            if "/search/" in url:
                return {"total_count": 1, "items": [self.item(1)]}
            self.assertIn("/pulls/1", url)
            return self.detail(1, body=None)

        result = self.run_sync(request)
        self.assertEqual(result["metrics"]["mergedPrs"], 1)
        self.assertEqual(result["contributions"][0]["status"], "Merged")
        self.assertEqual(result["contributions"][0]["summary"], "")
        self.assertIn("repo:owner/project", parse_qs(urlparse(urls[0]).query)["q"][0])

    def test_paginates_and_counts_before_limiting_display(self):
        pages = []

        def request(url):
            if "/search/" in url:
                page = int(parse_qs(urlparse(url).query)["page"][0])
                pages.append(page)
                numbers = range(1, 101) if page == 1 else [101]
                return {"total_count": 101, "items": [self.item(n) for n in numbers]}
            return self.detail(int(url.rsplit("/", 1)[1]))

        result = self.run_sync(request)
        self.assertEqual(pages, [1, 2])
        self.assertEqual(result["metrics"]["mergedPrs"], 101)
        self.assertEqual(len(result["contributions"]), 12)

    def test_merged_contributions_sort_first_by_full_date(self):
        def request(url):
            if "/search/" in url:
                return {"total_count": 3, "items": [self.item(n) for n in (1, 2, 3)]}
            number = int(url.rsplit("/", 1)[1])
            detail = self.detail(number, merged=number != 3)
            if number == 2:
                detail["merged_at"] = "2026-10-03T10:00:00Z"
            return detail

        records = self.run_sync(request)["contributions"]
        self.assertEqual([record["number"] for record in records], [2, 1, 3])

    def test_unchanged_upstream_keeps_existing_file_and_timestamp(self):
        def request(url):
            if "/search/" in url:
                return {"total_count": 1, "items": [self.item(1)]}
            return self.detail(1)

        result = self.run_sync(request)
        result["generatedAt"] = "2020-01-01T00:00:00Z"
        self.output.write_text(json.dumps(result), encoding="utf-8")
        before = self.output.read_bytes()
        self.run_sync(request)
        self.assertEqual(self.output.read_bytes(), before)

    def test_changed_upstream_replaces_snapshot(self):
        self.output.write_text(json.dumps({"generatedAt": "2020-01-01T00:00:00Z", "metrics": {"mergedPrs": 0}, "contributions": []}), encoding="utf-8")

        def request(url):
            return {"total_count": 1, "items": [self.item(1)]} if "/search/" in url else self.detail(1)

        self.assertNotEqual(self.run_sync(request)["generatedAt"], "2020-01-01T00:00:00Z")

    def test_duplicate_results_are_counted_once(self):
        def request(url):
            return {"total_count": 2, "items": [self.item(1), self.item(1)]} if "/search/" in url else self.detail(1)

        self.assertEqual(self.run_sync(request)["metrics"]["mergedPrs"], 1)

    def test_closed_unmerged_pr_is_not_counted_as_merged(self):
        def request(url):
            if "/search/" in url:
                return {"total_count": 1, "items": [self.item(1)]}
            detail = self.detail(1, merged=False)
            detail["state"] = "closed"
            return detail

        result = self.run_sync(request)
        self.assertEqual(result["metrics"]["mergedPrs"], 0)
        self.assertEqual(result["contributions"][0]["status"], "Closed")

    def test_incomplete_search_keeps_previous_snapshot(self):
        for response in (
            {"total_count": 1001, "items": []},
            {"total_count": 1, "incomplete_results": True, "items": []},
            {"total_count": 1, "items": []},
        ):
            with self.subTest(response=response):
                self.output.write_text("previous snapshot", encoding="utf-8")
                with patch.object(sync_github, "request_json", return_value=response):
                    with self.assertRaises(RuntimeError):
                        sync_github.main()
                self.assertEqual(self.output.read_text(encoding="utf-8"), "previous snapshot")


if __name__ == "__main__":
    unittest.main()
