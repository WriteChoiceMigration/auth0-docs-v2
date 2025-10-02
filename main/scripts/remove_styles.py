#!/usr/bin/env python3
"""Remove inline <style> tags from locale docs listed in pages_paths.json."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_JSON = SCRIPT_DIR / "pages_paths.json"
STYLE_PATTERN = re.compile(
    r"<style\b[^>]*>.*?</style>", re.DOTALL | re.IGNORECASE
)
SEARCH_PREFIXES = (Path("main"), Path("output_docs_translated"))


def resolve_search_roots() -> list[Path]:
    """Return unique roots to search when resolving relative paths."""
    roots: list[Path] = []
    for root in (Path.cwd().resolve(), REPO_ROOT):
        if root not in roots:
            roots.append(root)
    return roots


def resolve_path(relative: Path) -> Path | None:
    """Return the first existing absolute path for the given relative path."""
    candidates = [relative]
    candidates.extend(prefix / relative for prefix in SEARCH_PREFIXES)

    roots = resolve_search_roots()
    seen: set[Path] = set()

    for candidate in candidates:
        if candidate.is_absolute():
            resolved = candidate
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.exists():
                return resolved
            continue

        for root in roots:
            resolved = (root / candidate).resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.exists():
                return resolved

    return None


def format_path(path: Path) -> str:
    """Return repo-relative paths for display when available."""
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def process_file(path: Path) -> bool:
    """Strip <style>...</style> blocks. Return True on change."""
    text = path.read_text(encoding="utf-8")
    new_text, count = STYLE_PATTERN.subn("", text)
    if count == 0:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    json_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON
    if not json_arg.exists() and not json_arg.is_absolute():
        candidates = [Path.cwd() / json_arg, SCRIPT_DIR / json_arg, REPO_ROOT / json_arg]
        for candidate in candidates:
            if candidate.exists():
                json_arg = candidate
                break
    if not json_arg.exists():
        raise SystemExit(f"JSON file not found: {json_arg}")

    paths = json.loads(json_arg.read_text(encoding="utf-8"))

    updated = 0
    skipped = 0
    for raw in paths:
        relative = Path(raw)
        resolved = resolve_path(relative)
        if resolved is None:
            print(f"[MISSING] {format_path(relative)}")
            skipped += 1
            continue

        if process_file(resolved):
            updated += 1
            print(f"[UPDATED] {format_path(resolved)}")
        else:
            skipped += 1
            print(f"[SKIPPED] {format_path(resolved)} -> No <style> tags")

    print(f"Done. Updated {updated} file(s), skipped {skipped}.")


if __name__ == "__main__":
    main()
