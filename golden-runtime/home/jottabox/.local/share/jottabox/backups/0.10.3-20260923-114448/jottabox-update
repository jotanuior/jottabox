#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
STATE_DIR="$HOME/.local/share/jottabox"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$STATE_DIR"

curl -fsSL "$RAW/manifest.json" -o "$TMP/manifest.json"

REMOTE="$(python3 - "$TMP/manifest.json" <<'PY'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8"))
print(m["version"])
PY
)"

SCRIPT="$(python3 - "$TMP/manifest.json" <<'PY'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8"))
print(m["update_script"])
PY
)"

LOCAL="$(cat "$STATE_DIR/VERSION" 2>/dev/null || true)"
if [[ -z "$LOCAL" && -f "$STATE_DIR/jottabox.sh" ]]; then
  LOCAL="$(grep -m1 '^VERSION=' "$STATE_DIR/jottabox.sh" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)"
fi
[[ -n "$LOCAL" ]] || LOCAL="legado"

echo "Instalada:   $LOCAL"
echo "Disponível: $REMOTE"

if [[ "$LOCAL" == "$REMOTE" ]]; then
  echo "JottaBox já está atualizado."
  exit 0
fi

echo
echo "Novidades:"
python3 - "$TMP/manifest.json" <<'PY'
import json,sys
for n in json.load(open(sys.argv[1],encoding="utf-8")).get("notes",[]):
    print(" - "+n)
PY

echo
read -rp "Atualizar para $REMOTE? [s/N] " yn
[[ "$yn" =~ ^[sSyY]$ ]] || exit 0

curl -fsSL "$RAW/$SCRIPT" -o "$TMP/update.sh"
bash -n "$TMP/update.sh"
chmod +x "$TMP/update.sh"
"$TMP/update.sh"
