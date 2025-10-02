#!/usr/bin/env python3
"""
Script to find and report unique Tooltip components in Japanese MDX files.
Reports the first occurrence of each unique tooltip text.
"""

import json
import re
from pathlib import Path
from collections import OrderedDict


def find_tooltip_content(text):
    """Extract tooltip content and id from various Tooltip component formats."""
    tooltips = []

    # Pattern to match <Tooltip>content</Tooltip>
    pattern1 = r"<Tooltip([^>]*)>(.*?)</Tooltip>"
    matches1 = re.finditer(pattern1, text, re.DOTALL)
    for match in matches1:
        attrs = match.group(1)
        content = match.group(2).strip()

        # Extract id if present
        id_match = re.search(r'id=["\'](.*?)["\']', attrs)
        tooltip_id = id_match.group(1) if id_match else None

        tooltips.append({"content": content, "id": tooltip_id})

    # Pattern to match self-closing <Tooltip ... /> with content or tip prop
    pattern2 = r"<Tooltip\s+([^>]*?)/>"
    matches2 = re.finditer(pattern2, text, re.DOTALL)
    for match in matches2:
        attrs = match.group(1)

        # Try to extract content from tip or content attribute
        tip_match = re.search(r'(?:tip|content)=["\'](.*?)["\']', attrs)
        content = tip_match.group(1).strip() if tip_match else None

        # Extract id if present
        id_match = re.search(r'id=["\'](.*?)["\']', attrs)
        tooltip_id = id_match.group(1) if id_match else None

        if content:
            tooltips.append({"content": content, "id": tooltip_id})

    return tooltips


def scan_directory(directory):
    """Scan directory for MDX files and find all unique tooltips."""
    tooltip_map = OrderedDict()  # {tooltip_content: {'file': path, 'id': id}}

    # Find all .mdx files
    mdx_files = list(Path(directory).rglob("*.mdx"))

    for file_path in sorted(mdx_files):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tooltips = find_tooltip_content(content)

            for tooltip in tooltips:
                tooltip_content = tooltip["content"]
                tooltip_id = tooltip["id"]

                # Only store first occurrence of each unique tooltip content
                if tooltip_content and tooltip_content not in tooltip_map:
                    relative_path = file_path.relative_to(Path(directory).parent)
                    tooltip_map[tooltip_content] = {
                        "file": str(relative_path),
                        "id": tooltip_id,
                    }

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return tooltip_map


def main():
    directory = "/home/raeder/mintlify/auth0-docs-v2/main/docs/fr-ca"
    output_file = "/home/raeder/mintlify/auth0-docs-v2/main/tooltip_report.json"

    print("Scanning for Tooltip components in Japanese MDX files...\n")

    tooltip_map = scan_directory(directory)

    if not tooltip_map:
        print("No Tooltip components found.")
        return

    # Convert to list format for JSON
    tooltips_list = [
        {"content": content, "id": info["id"], "file": info["file"]}
        for content, info in tooltip_map.items()
    ]

    # Create report structure
    report = {"total_unique_tooltips": len(tooltips_list), "tooltips": tooltips_list}

    # Write to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Found {len(tooltips_list)} unique tooltip(s)")
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()
