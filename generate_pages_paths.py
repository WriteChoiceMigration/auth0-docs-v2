#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

PAGES_FILE = Path("pages.txt")
OUTPUT_FILE = Path("pages_paths.json")
PREFIX = "output_docs_translated/docs/fr-ca/"

pattern = re.compile(r"(output_docs_translated/docs/fr-ca/[\w\-/\.]+)")


def main() -> None:
    if not PAGES_FILE.exists():
        raise SystemExit(f"Arquivo nao encontrado: {PAGES_FILE}")

    unique_paths: list[str] = []
    seen = set()

    for raw_line in PAGES_FILE.read_text().splitlines():
        if PREFIX not in raw_line:
            continue

        match = pattern.search(raw_line)
        if not match:
            continue

        path = match.group(1)
        if path in seen:
            continue

        seen.add(path)
        unique_paths.append(path)

    OUTPUT_FILE.write_text(json.dumps(unique_paths, indent=2))


if __name__ == "__main__":
    main()
