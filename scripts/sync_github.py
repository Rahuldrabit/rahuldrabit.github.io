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


def main() -> int:
    if not os.environ.get("GITHUB_TOKEN"):
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 2

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    query = urllib.parse.quote(config["query"])
    search_url = f"https://api.github.com/search/issues?q={query}&per_page=100"
    search_result = request_json(search_url)
    approved = {repo.lower() for repo in config["approvedRepositories"]}
    contributions = []

    for item in search_result.get("items", []):
        repository = item["repository_url"].removeprefix("https://api.github.com/repos/")
        if repository.lower() not in approved:
            continue
        detail = request_json(item["url"])
        merged_at = detail.get("merged_at")
        contributions.append(
            {
                "repository": repository,
                "number": detail["number"],
                "title": detail["title"],
                "summary": detail.get("body", "").split("\n", 1)[0][:240],
                "status": "Merged" if merged_at else detail["state"].title(),
                "mergedAt": short_date(merged_at),
                "updatedAt": short_date(detail.get("updated_at")),
                "url": detail["html_url"],
            }
        )

    contributions.sort(key=lambda item: (item["status"] != "Merged", item["updatedAt"], item["repository"], item["number"]), reverse=True)
    contributions = contributions[: config.get("maxContributions", 12)]
    merged_prs = sum(item["status"] == "Merged" for item in contributions)
    output = {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "metrics": {"mergedPrs": merged_prs},
        "contributions": contributions,
    }
    serialized = json.dumps(output, indent=2, ensure_ascii=True) + "\n"
    current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
    if current != serialized:
        OUTPUT_PATH.write_text(serialized, encoding="utf-8")
        print(f"Updated {OUTPUT_PATH} with {len(contributions)} contributions")
    else:
        print("GitHub snapshot is unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
