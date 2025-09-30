from pathlib import Path


def process_files(directory):
    """Process all files in directory recursively, replacing content with frontmatter."""
    dir_path = Path(directory)

    if not dir_path.exists():
        print(f"Directory {directory} does not exist")
        return

    for file_path in dir_path.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip files named 'interactive'
        if "interactive" in file_path.stem:
            print(f"Skipping {file_path.name}")
            continue

        # Build the URL path
        # Remove 'main/' from start and 'ja-jp/' from path
        full_path = str(file_path)
        url_path = (
            full_path.replace("main", "", 1).replace("fr-ca/", "").replace(".mdx", "")
        )

        # Create frontmatter content
        new_content = f"""---
url: {url_path}
---
"""

        # Write the new content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"Processed {file_path} -> url: {url_path}")


if __name__ == "__main__":
    directory = "main/docs/fr-ca/quickstart/"
    process_files(directory)
    print("\nDone!")
