#!/usr/bin/env python3
"""Validate the static site's local data contracts."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REQUIRED_KEYS = {
    "github.json": {"generatedAt", "metrics", "contributions"},
    "github-sync.json": {"username", "approvedRepositories", "maxContributions"},
}


def main() -> int:
    errors = []
    for path in sorted(DATA.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{path.name}: invalid JSON: {error}")
            continue
        missing = REQUIRED_KEYS.get(path.name, set()) - set(value) if isinstance(value, dict) else set()
        if missing:
            errors.append(f"{path.name}: missing keys: {', '.join(sorted(missing))}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(list(DATA.glob('*.json')))} JSON data files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
