#!/usr/bin/env bash
set -Eeuo pipefail
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

echo ">>> Migrando para a base autocontida JottaBox 0.11.0"
curl -fsSL   -H 'Accept: application/vnd.github.raw+json'   -H 'Cache-Control: no-cache, no-store, max-age=0'   "https://api.github.com/repos/jotanuior/jottabox/contents/install.sh?ref=main"   -o "$TMP"

bash "$TMP"

echo "0.11.0" > "$HOME/.local/share/jottabox/VERSION"
