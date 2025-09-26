#!/usr/bin/env python3
"""Remove inline <style> tags from locale docs listed in pages_paths.json."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DEFAULT_JSON = Path("pages_paths.json")
STYLE_PATTERN = re.compile(r"<style\b[^>]*>.*?</style>", re.DOTALL | re.IGNORECASE)
SEARCH_PREFIXES = (Path("."), Path("main"), Path("output_docs_translated"))


def resolve_path(relative: Path) -> Path | None:
    """Return the first existing path when checking known prefixes."""
    seen: set[Path] = set()
    for prefix in SEARCH_PREFIXES:
        candidate = (prefix / relative).resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            return candidate
    return None


def process_file(path: Path) -> bool:
    """Strip <style>...</style> blocks. Return True on change."""
    text = path.read_text(encoding="utf-8")
    new_text, count = STYLE_PATTERN.subn("", text)
    if count == 0:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON
    if not json_path.exists():
        raise SystemExit(f"JSON file not found: {json_path}")

    paths = json.loads(json_path.read_text(encoding="utf-8"))

    updated = 0
    skipped = 0
    for raw in paths:
        relative = Path(raw)
        resolved = resolve_path(relative)
        if resolved is None:
            print(f"[MISSING] {relative}")
            skipped += 1
            continue

        if process_file(resolved):
            updated += 1
            print(f"[UPDATED] {resolved}")
        else:
            skipped += 1
            print(f"[SKIPPED] {resolved} -> No <style> tags")

    print(f"Done. Updated {updated} file(s), skipped {skipped}.")


if __name__ == "__main__":
    main()
