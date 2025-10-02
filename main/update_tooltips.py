#!/usr/bin/env python3

import json
import os
import re
from pathlib import Path


def load_tooltip_data(json_path):
    """Load tooltip data and create a lookup map by content."""
    with open(json_path, "r", encoding="utf-8") as f:
        tooltip_data = json.load(f)

    # Create a map for quick lookup by content
    tooltip_map = {}
    for item in tooltip_data:
        tooltip_map[item["content"]] = item

    return tooltip_map


def find_mdx_files(directory):
    """Recursively find all .mdx files in the directory."""
    mdx_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".mdx"):
                mdx_files.append(os.path.join(root, file))
    return mdx_files


def update_tooltips(content, tooltip_map, lang="fr-ca"):
    """Update Tooltip components in the content."""
    replacement_count = 0

    # Regular expression to match Tooltip components
    # Matches: <Tooltip data-tooltip-id="..." tip="...">content</Tooltip>
    tooltip_pattern = (
        r'<Tooltip\s+data-tooltip-id="[^"]*"\s+tip="[^"]*">([^<]+)</Tooltip>'
    )

    def replace_tooltip(match):
        nonlocal replacement_count
        inner_text = match.group(1)

        # Look up the tooltip data by the inner text
        tooltip_info = tooltip_map.get(inner_text)

        if (
            tooltip_info
            and tooltip_info.get("href")
            and tooltip_info.get("tooltip_text")
        ):
            replacement_count += 1
            # Transform the href URL
            # From: https://auth0.com/docs/glossary?term=...
            # To: /docs/{lang}/glossary?term=...
            original_href = tooltip_info["href"]
            if "auth0.com/docs/" in original_href:
                transformed_href = original_href.replace(
                    "https://auth0.com/docs/", f"/docs/{lang}/"
                )
            else:
                transformed_href = original_href

            # Return the updated Tooltip component with href, tip, and cta
            tip_text = tooltip_info["tooltip_text"]
            return f'<Tooltip href="{transformed_href}" tip="{tip_text}" cta="Voir le glossaire">{inner_text}</Tooltip>'

        # If no match found, return original
        return match.group(0)

    updated_content = re.sub(tooltip_pattern, replace_tooltip, content)

    return updated_content, replacement_count


def main():
    """Main execution function."""
    script_dir = Path(__file__).parent
    docs_dir = script_dir / "docs" / "fr-ca"
    json_path = script_dir / "tooltip_content.json"
    lang = "fr-ca"  # Language code for URL transformation

    print("Loading tooltip data...")
    tooltip_map = load_tooltip_data(json_path)
    print(f"Loaded {len(tooltip_map)} tooltip entries")

    print("\nFinding MDX files...")
    mdx_files = find_mdx_files(docs_dir)
    print(f"Found {len(mdx_files)} MDX files")

    total_replacements = 0
    files_modified = 0

    for file_path in mdx_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        updated_content, count = update_tooltips(content, tooltip_map, lang)

        if count > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            files_modified += 1
            total_replacements += count
            relative_path = os.path.relpath(file_path, docs_dir)
            print(f"Updated {count} tooltips in: {relative_path}")

    print("\n=== Summary ===")
    print(f"Files processed: {len(mdx_files)}")
    print(f"Files modified: {files_modified}")
    print(f"Total tooltips updated: {total_replacements}")


if __name__ == "__main__":
    main()
