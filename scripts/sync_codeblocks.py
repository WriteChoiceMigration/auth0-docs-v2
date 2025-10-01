#!/usr/bin/env python3
"""Replace ja-jp codeblocks with originals using paths listed in JSON."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CODEBLOCK_PATTERN = re.compile(r"```[^\n]*\n.*?```", re.DOTALL)
DEFAULT_JSON = Path("pages_paths.json")
LOCALE_SEGMENT = "ja-jp"
SEARCH_PREFIXES = (Path("main"), Path("output_docs_translated"))
CODEGROUP_PATTERN = re.compile(r"<CodeGroup\b.*?</CodeGroup>", re.DOTALL)


@dataclass
class SyncOutcome:
    changed: bool
    message: str


@dataclass
class Segment:
    start: int
    end: int
    text: str


def list_segments(pattern: re.Pattern[str], text: str) -> list[Segment]:
    """Return spans and contents for the provided regex pattern."""
    return [Segment(m.start(), m.end(), m.group(0)) for m in pattern.finditer(text)]


def list_codeblocks(text: str) -> list[Segment]:
    """Return spans and contents for fenced codeblocks."""
    return list_segments(CODEBLOCK_PATTERN, text)


def list_codegroups(text: str) -> list[Segment]:
    """Return spans and contents for <CodeGroup> components."""
    return list_segments(CODEGROUP_PATTERN, text)


def remove_locale_segment(path: Path, locale: str = LOCALE_SEGMENT) -> Path:
    """Drop the locale segment (e.g. ja-jp) from the given relative path."""
    parts = []
    locale_removed = False
    for part in path.parts:
        if not locale_removed and part == locale:
            locale_removed = True
            continue
        parts.append(part)
    if not locale_removed:
        raise ValueError(f"Locale segment '{locale}' not found in path: {path}")
    return Path(*parts)


def resolve_locale_path(relative: Path) -> Path | None:
    """Return the first existing path for the locale file, testing known prefixes."""
    candidates = [relative]
    for prefix in SEARCH_PREFIXES:
        candidates.append(prefix / relative)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def replace_segments(
    locale_text: str,
    locale_segments: list[Segment],
    replacements: list[str],
    label: str,
    *,
    strict: bool,
) -> tuple[str, bool, str | None]:
    """Replace locale segments with originals, ensuring counts stay aligned."""
    locale_count = len(locale_segments)
    original_count = len(replacements)

    if locale_count == 0 and original_count == 0:
        return locale_text, False, None

    plural_label = f"{label}s"

    if original_count == 0:
        message = f"Original has no {plural_label}"
        if strict:
            raise ValueError(message)
        return locale_text, False, message

    if locale_count == 0:
        message = f"Locale has no {plural_label}"
        if strict:
            raise ValueError(message)
        return locale_text, False, message

    if locale_count != original_count:
        message = (
            f"Mismatch in {label} count: locale={locale_count} original={original_count}"
        )
        if strict:
            raise ValueError(message)
        return locale_text, False, message

    result_parts: list[str] = []
    last_idx = 0
    for segment, replacement in zip(locale_segments, replacements):
        result_parts.append(locale_text[last_idx:segment.start])
        result_parts.append(replacement)
        last_idx = segment.end
    result_parts.append(locale_text[last_idx:])

    new_text = "".join(result_parts)
    return new_text, new_text != locale_text, None


def sync_file(locale_path: Path, original_path: Path) -> SyncOutcome:
    """Synchronize codeblocks from original into the locale-specific file."""
    locale_text = locale_path.read_text(encoding="utf-8")
    original_text = original_path.read_text(encoding="utf-8")

    locale_groups = list_codegroups(locale_text)
    original_groups = [segment.text for segment in list_codegroups(original_text)]

    groups_present = bool(locale_groups or original_groups)
    groups_changed = False
    messages: list[str] = []

    if groups_present:
        try:
            locale_text, groups_changed, msg = replace_segments(
                locale_text,
                locale_groups,
                original_groups,
                "CodeGroup",
                strict=True,
            )
        except ValueError as exc:
            return SyncOutcome(False, f"Skipped: {exc}")
        if msg:
            messages.append(msg)
    
    locale_blocks = list_codeblocks(locale_text)
    original_blocks = [segment.text for segment in list_codeblocks(original_text)]

    blocks_present = bool(locale_blocks or original_blocks)
    blocks_changed = False
    if blocks_present:
        locale_text, blocks_changed, msg = replace_segments(
            locale_text,
            locale_blocks,
            original_blocks,
            "codeblock",
            strict=False,
        )
        if msg:
            messages.append(msg)

    if not groups_present and not blocks_present:
        return SyncOutcome(False, "No codeblocks or CodeGroups in either file")

    if not (groups_changed or blocks_changed):
        if messages:
            return SyncOutcome(False, "; ".join(messages))
        return SyncOutcome(False, "Already matched")

    locale_path.write_text(locale_text, encoding="utf-8")
    summary = "; ".join(messages) if messages else "Updated"
    return SyncOutcome(True, summary)


def main() -> None:
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON
    if not json_path.exists():
        raise SystemExit(f"JSON file not found: {json_path}")

    paths = json.loads(json_path.read_text(encoding="utf-8"))

    updated = 0
    skipped = 0
    for relative in paths:
        relative_path = Path(relative)
        locale_path = resolve_locale_path(relative_path)
        if locale_path is None:
            print(f"[MISSING] {relative_path}")
            skipped += 1
            continue

        try:
            original_path = remove_locale_segment(locale_path)
        except ValueError as exc:
            print(f"[ERROR] {locale_path}: {exc}")
            skipped += 1
            continue

        if not original_path.exists():
            print(f"[MISSING ORIGINAL] {locale_path} -> {original_path}")
            skipped += 1
            continue

        outcome = sync_file(locale_path, original_path)
        label = "UPDATED" if outcome.changed else "SKIPPED"
        print(f"[{label}] {locale_path} -> {outcome.message}")

        if outcome.changed:
            updated += 1
        else:
            skipped += 1

    print(f"Done. Updated {updated} file(s), skipped {skipped}.")


if __name__ == "__main__":
    main()
