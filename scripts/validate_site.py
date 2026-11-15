#!/usr/bin/env python3
"""Validate all required portfolio datasets and their rendering contracts."""

import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
COLLECTION_FIELDS = {
    "research.json": ("title",),
    "publications.json": ("title",),
    "experience.json": ("period", "role", "organization", "description"),
    "projects.json": ("title", "category", "description"),
    "education.json": ("degree", "institution", "period"),
    "skills.json": ("name",),
}
REQUIRED_FILES = {*COLLECTION_FIELDS, "profile.json", "github.json", "github-sync.json"}
PROJECT_CATEGORIES = {"live-product", "engineering-framework", "research-system", "research-project"}


def validate_data(filename: str, value) -> list[str]:
    errors = []

    def error(field, message):
        errors.append(f"{filename}{field}: {message}")

    def text(record, field, location="", required=True):
        if field not in record and not required:
            return
        item = record.get(field)
        if not isinstance(item, str) or not item.strip():
            error(f"{location}.{field}", "expected a nonempty string")

    def strings(record, field, location="", required=False):
        if field not in record and not required:
            return
        items = record.get(field)
        if not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items):
            error(f"{location}.{field}", "expected an array of nonempty strings")

    def url(item, location):
        if not isinstance(item, str) or not item.strip():
            error(location, "expected a nonempty URL")
            return
        try:
            parsed = urlparse(item)
            valid = (
                parsed.scheme in ("http", "https") and bool(parsed.netloc)
                or parsed.scheme == "mailto" and bool(parsed.path)
                or not parsed.scheme and not parsed.netloc and bool(parsed.path)
            )
        except ValueError:
            valid = False
        if not valid:
            error(location, "expected an HTTP, HTTPS, mailto, or relative URL")

    def records(items, location=""):
        if not isinstance(items, list):
            error(location, "expected an array of records")
            return []
        result = []
        for index, item in enumerate(items):
            entry = f"{location}[{index}]"
            if not isinstance(item, dict):
                error(entry, "expected an object")
            else:
                result.append((item, entry))
        return result

    if filename in COLLECTION_FIELDS:
        for record, location in records(value):
            for field in COLLECTION_FIELDS[filename]:
                text(record, field, location)
            for field in ("area", "status", "location", "type", "venue", "date", "doi"):
                text(record, field, location, required=False)
            if "url" in record:
                url(record["url"], f"{location}.url")
            strings(record, "tags", location)
            if filename == "skills.json":
                strings(record, "items", location, required=True)
            if filename == "projects.json":
                if record.get("category") not in PROJECT_CATEGORIES:
                    error(f"{location}.category", "unknown project category")
                if "featured" in record and type(record["featured"]) is not bool:
                    error(f"{location}.featured", "expected a boolean")
            if "year" in record and (type(record["year"]) not in (int, str) or not str(record["year"]).strip()):
                error(f"{location}.year", "expected a year string or integer")
            if "links" in record:
                for link, link_location in records(record["links"], f"{location}.links"):
                    text(link, "label", link_location)
                    url(link.get("url"), f"{link_location}.url")
        return errors

    if filename not in REQUIRED_FILES:
        return errors
    if not isinstance(value, dict):
        error("", "expected an object")
        return errors

    if filename == "profile.json":
        for field in ("name", "role", "location", "institution", "email"):
            text(value, field)
        links = value.get("links")
        if not isinstance(links, dict):
            error(".links", "expected an object of profile URLs")
        else:
            for name, item in links.items():
                url(item, f".links.{name}")
    elif filename == "github-sync.json":
        text(value, "username")
        text(value, "query")
        strings(value, "approvedRepositories", required=True)
        repositories = value.get("approvedRepositories")
        if isinstance(repositories, list) and (not repositories or any(not isinstance(repo, str) or len(repo.split("/")) != 2 or not all(repo.split("/")) for repo in repositories)):
            error(".approvedRepositories", "expected at least one owner/repository name")
        maximum = value.get("maxContributions")
        if type(maximum) is not int or maximum <= 0:
            error(".maxContributions", "expected a positive integer")
        if "reviewRequired" in value and type(value["reviewRequired"]) is not bool:
            error(".reviewRequired", "expected a boolean")
    elif filename == "github.json":
        text(value, "generatedAt")
        try:
            timestamp = datetime.fromisoformat(value.get("generatedAt", "").replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError("missing timezone")
        except (ValueError, AttributeError, TypeError):
            error(".generatedAt", "expected an ISO timestamp with a timezone")
        metrics = value.get("metrics")
        merged = metrics.get("mergedPrs") if isinstance(metrics, dict) else None
        if type(merged) is not int or merged < 0:
            error(".metrics.mergedPrs", "expected a nonnegative integer")
        displayed_merged = 0
        for record, location in records(value.get("contributions"), ".contributions"):
            for field in ("repository", "title", "status"):
                text(record, field, location)
            url(record.get("url"), f"{location}.url")
            if type(record.get("number")) is not int or record["number"] <= 0:
                error(f"{location}.number", "expected a positive integer")
            for field in ("summary", "mergedAt", "updatedAt"):
                if field in record and not isinstance(record[field], str):
                    error(f"{location}.{field}", "expected a string")
            displayed_merged += record.get("status") == "Merged"
        if type(merged) is int and merged < displayed_merged:
            error(".metrics.mergedPrs", "cannot be less than displayed merged contributions")
    return errors


def main() -> int:
    errors = []
    paths = sorted(DATA.glob("*.json"))
    for filename in sorted(REQUIRED_FILES - {path.name for path in paths}):
        errors.append(f"{filename}: required data file is missing")
    for path in paths:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append(f"{path.name}: could not read JSON: {error}")
            continue
        errors.extend(validate_data(path.name, value))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(paths)} JSON data files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
