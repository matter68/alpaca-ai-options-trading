#!/usr/bin/env python3
"""Upload a single file to GitHub repo via REST API."""
import os, sys, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
TOKEN = os.getenv("ALPACA_API_KEY", "")  # Using same env for PAT (user will update)
REPO_OWNER = "matter68"
REPO_NAME = "alpaca-ai-options-trading"

if len(sys.argv) < 2:
    print("Usage: upload_single.py <filepath>")
    sys.exit(1)

file_path = sys.argv[1]
p = Path(file_path)
if not p.exists():
    print(f"File not found: {file_path}")
    sys.exit(1)

import requests
content = p.read_bytes()
encoded = __import__("base64").b64encode(content).decode()
github_path = p.name

url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{github_path}"
headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

# Check if file exists to get SHA
r = requests.get(url, headers=headers)
sha = None
if r.status_code == 200:
    sha = r.json().get("sha")
    print(f"File exists (SHA: {sha}), will update")
elif r.status_code != 404:
    print(f"Error checking file: {r.status_code} {r.text}")
    sys.exit(1)

payload = {
    "message": f"Add {github_path} - flash test validation",
    "content": encoded,
}
if sha:
    payload["sha"] = sha

r2 = requests.put(url, headers=headers, json=payload)
if r2.status_code in (200, 201):
    print(f"✅ Uploaded {github_path} successfully")
else:
    print(f"❌ Upload failed: {r2.status_code} {r2.text}")
    sys.exit(1)
