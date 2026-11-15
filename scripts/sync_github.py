#!/usr/bin/env python3
"""Create a deterministic, reviewable GitHub snapshot for the portfolio."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "github-sync.json"
OUTPUT_PATH = ROOT / "data" / "github.json"


def request_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "rahuldrabit-portfolio-sync",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def short_date(value: str | None) -> str:
    return value[:7] if value else ""


def search_repository(query: str, repository: str):
    """Paginate each approved repository so unrelated PRs cannot hide its results."""
    page = 1
    fetched = 0
    while True:
        parameters = urllib.parse.urlencode(
            {"q": f"{query} repo:{repository}", "per_page": 100, "page": page}
        )
        result = request_json(f"https://api.github.com/search/issues?{parameters}")
        if result.get("incomplete_results") or result.get("total_count", 0) > 1000:
            raise RuntimeError(f"GitHub search is incomplete for {repository}; keep the existing snapshot")
        items = result.get("items", [])
        yield from items
        fetched += len(items)
        if fetched >= result.get("total_count", fetched):
            return
        if not items:
            raise RuntimeError(f"GitHub search pagination stopped early for {repository}")
        page += 1


def main() -> int:
    if not os.environ.get("GITHUB_TOKEN"):
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 2

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    approved = {repo.lower() for repo in config["approvedRepositories"]}
    contributions = []
    seen = set()

    for approved_repository in sorted(approved):
        for item in search_repository(config["query"], approved_repository):
            repository = item["repository_url"].removeprefix("https://api.github.com/repos/")
            identity = (repository.lower(), item["number"])
            pull_request = item.get("pull_request")
            if repository.lower() not in approved or not pull_request or identity in seen:
                continue
            seen.add(identity)
            detail = request_json(pull_request["url"])
            merged_at = detail.get("merged_at")
            record = {
                "repository": repository,
                "number": detail["number"],
                "title": detail["title"],
                "summary": (detail.get("body") or "").split("\n", 1)[0][:240],
                "status": "Merged" if merged_at else detail["state"].title(),
                "mergedAt": short_date(merged_at),
                "updatedAt": short_date(detail.get("updated_at")),
                "url": detail["html_url"],
            }
            contributions.append((record, merged_at or detail.get("updated_at") or ""))

    contributions.sort(
        key=lambda item: (item[0]["status"] == "Merged", item[1], item[0]["repository"], item[0]["number"]),
        reverse=True,
    )
    merged_prs = sum(record["status"] == "Merged" for record, _ in contributions)
    payload = {
        "metrics": {"mergedPrs": merged_prs},
        "contributions": [record for record, _ in contributions[: config.get("maxContributions", 12)]],
    }
    current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
    try:
        previous = json.loads(current)
    except json.JSONDecodeError:
        previous = {}
    if isinstance(previous, dict) and previous.get("generatedAt") and all(previous.get(key) == value for key, value in payload.items()):
        print("GitHub snapshot is unchanged")
        return 0
    output = {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        **payload,
    }
    serialized = json.dumps(output, indent=2, ensure_ascii=True) + "\n"
    OUTPUT_PATH.write_text(serialized, encoding="utf-8")
    print(f"Updated {OUTPUT_PATH} with {len(payload['contributions'])} contributions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
