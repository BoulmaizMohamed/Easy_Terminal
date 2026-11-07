"""Upload release binaries and user guides to GitHub Releases."""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = "BoulmaizMohamed/Easy_Terminal"
TAG = "v1.0.0"
TITLE = "Easy_Terminal v1.0.0 - Official Release"

RELEASE_BODY = """## ⚡ Easy_Terminal v1.0.0

The modern, safe, and visual Windows Command Center built with Python & Textual.

### 📥 Downloads:
- **`Easy_Terminal-Setup.exe`**: Native Windows Setup Wizard (guided installer, Start menu & desktop shortcuts, Explorer context menu integration).
- **`Easy_Terminal-Portable.zip`**: Standalone portable edition. Extract and run anywhere without administrator privileges.
- **`Easy_Terminal_User_Guide.pdf`**: Printable 7-page comprehensive guide in English.
- **`Easy_Terminal_Guide_Utilisateur.pdf`**: Guide complet imprimable en français.

### ✨ Key Features:
- **529 Categorized Windows Commands** with instant search and documentation.
- **Interactive Parameter Form Builder** for error-free argument configuration.
- **Dual Persistent Shells** (PowerShell & CMD) with real-time output.
- **Git Auto-Discovery (`Ctrl+G`)** to switch projects in milliseconds.
- **Destructive Command Guard** preventing accidental file or disk deletion.
- **Bilingual Interface** in English and French.

**Full Changelog**: https://github.com/BoulmaizMohamed/Easy_Terminal/commits/v1.0.0
"""


def get_token() -> str:
    res = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n",
        capture_output=True,
        text=True,
        check=True,
    )
    for line in res.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("Could not find GitHub token from git credentials.")


def api_request(url: str, token: str, data: bytes | None = None, method: str = "GET", headers: dict | None = None):
    req_headers = {
        "User-Agent": "Easy_Terminal_Release_Script",
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
        if not content:
            return None
        return json.loads(content.decode("utf-8"))


def main():
    root = Path(__file__).resolve().parent.parent
    token = get_token()
    print(f"==> Authenticated with GitHub as repository owner")

    # Check if release already exists
    releases_url = f"https://api.github.com/repos/{REPO}/releases"
    releases = api_request(releases_url, token)
    existing_release = next((r for r in releases if r.get("tag_name") == TAG), None)

    if existing_release:
        print(f"==> Release for {TAG} already exists (ID: {existing_release['id']})")
        release = existing_release
    else:
        print(f"==> Creating new GitHub Release for tag {TAG}...")
        create_payload = json.dumps({
            "tag_name": TAG,
            "target_commitish": "main",
            "name": TITLE,
            "body": RELEASE_BODY,
            "draft": False,
            "prerelease": False,
        }).encode("utf-8")
        release = api_request(
            releases_url,
            token,
            data=create_payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        print(f"==> Release created successfully! URL: {release['html_url']}")

    release_id = release["id"]
    upload_url_template = release["upload_url"]  # https://uploads.github.com/.../assets{?name,label}
    upload_base = upload_url_template.split("{")[0]

    # Existing asset filenames
    existing_assets = {a["name"]: a["id"] for a in release.get("assets", [])}

    assets_to_upload = [
        root / "dist" / "Easy_Terminal-Setup.exe",
        root / "dist" / "Easy_Terminal-Portable.zip",
        root / "docs" / "Easy_Terminal_User_Guide.pdf",
        root / "docs" / "Easy_Terminal_Guide_Utilisateur.pdf",
    ]

    for asset_path in assets_to_upload:
        if not asset_path.exists():
            print(f"⚠️  Asset not found: {asset_path}")
            continue

        filename = asset_path.name
        file_size = asset_path.stat().st_size
        print(f"\n--> Uploading {filename} ({file_size / (1024 * 1024):.2f} MB)...")

        # Delete existing asset if it exists to replace it cleanly
        if filename in existing_assets:
            asset_id = existing_assets[filename]
            print(f"    Deleting previous {filename} (Asset ID: {asset_id})...")
            delete_url = f"https://api.github.com/repos/{REPO}/releases/assets/{asset_id}"
            try:
                api_request(delete_url, token, method="DELETE")
            except Exception as e:
                print(f"    Warning during asset delete: {e}")

        # Upload
        content_type = "application/zip" if filename.endswith(".zip") else (
            "application/pdf" if filename.endswith(".pdf") else "application/octet-stream"
        )
        encoded_name = urllib.parse.quote(filename)
        upload_url = f"{upload_base}?name={encoded_name}"

        with open(asset_path, "rb") as f:
            data = f.read()

        req_headers = {
            "User-Agent": "Easy_Terminal_Release_Script",
            "Authorization": f"token {token}",
            "Content-Type": content_type,
            "Content-Length": str(len(data)),
        }
        req = urllib.request.Request(upload_url, data=data, headers=req_headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            print(f"    [OK] Uploaded: {resp_data.get('browser_download_url')}")

    print("\n" + "=" * 60)
    print("SUCCESS: GitHub Release v1.0.0 published with all assets!")
    print(f"View Release: {release['html_url']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
