#!/usr/bin/env python3
import json
import os
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def download_images():
    # Read the JSON file
    with open("missing-images.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Process each key and its URLs
    for base_path, urls in data.items():
        print(f"\nProcessing images for: {base_path}")

        for url in urls:
            try:
                # Parse the URL to extract the path after the domain
                parsed = urlparse(url)
                # Remove the leading slash and extract everything after 'images.ctfassets.net/'
                path_parts = parsed.path.lstrip("/").split("/")

                # Build the local path: base_path/rest_of_url_path
                # Skip the first part if it's a locale (ja-jp, fr-fr, etc.)
                if len(path_parts) > 0 and path_parts[0] in ["ja-jp", "fr-fr", "en-us"]:
                    # Skip the locale in the path since it's already in the key
                    image_subpath = "/".join(path_parts[1:])
                else:
                    image_subpath = "/".join(path_parts)

                local_path = os.path.join(base_path, image_subpath)

                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                # Download the image
                print(f"Downloading: {url}")
                print(f"Saving to: {local_path}")

                urllib.request.urlretrieve(url, local_path)
                print(f"✓ Successfully downloaded")

            except Exception as e:
                print(f"✗ Error downloading {url}: {e}")


if __name__ == "__main__":
    download_images()
