#!/usr/bin/env bash
set -Eeuo pipefail

REPO="jotanuior/jottabox"
API="https://api.github.com/repos/$REPO/contents"
STATE_DIR="$HOME/.local/share/jottabox"
BIN_DIR="$HOME/.local/bin"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$STATE_DIR" "$BIN_DIR"

api_file() {
  local path="$1" dest="$2"
  curl -fsSL     -H 'Accept: application/vnd.github.raw+json'     -H 'Cache-Control: no-cache, no-store, max-age=0'     "$API/$path?ref=main" -o "$dest"
}

restart_jottabox() {
  local launcher="$BIN_DIR/jottabox-console"
  [[ -x "$launcher" ]] || return 0
  setsid -f bash -lc "
    sleep 1.5
    pkill -f '[j]ottabox-console' 2>/dev/null || true
    sleep 1
    exec '$launcher'
  " >"$STATE_DIR/restart.log" 2>&1 || true
}

api_file manifest.json "$TMP/manifest.json"

REMOTE="$(python3 - "$TMP/manifest.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1],encoding="utf-8"))["version"])
PY
)"
SCRIPT="$(python3 - "$TMP/manifest.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1],encoding="utf-8"))["update_script"])
PY
)"
LOCAL="$(cat "$STATE_DIR/VERSION" 2>/dev/null || echo legado)"

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

api_file "$SCRIPT" "$TMP/update.sh"
bash -n "$TMP/update.sh"
chmod +x "$TMP/update.sh"
"$TMP/update.sh"

INSTALLED="$(cat "$STATE_DIR/VERSION" 2>/dev/null || true)"
if [[ "$INSTALLED" != "$REMOTE" ]]; then
  echo "ERRO: atualização terminou sem confirmar VERSION $REMOTE."
  exit 1
fi

echo
echo "Atualização concluída. Reiniciando JottaBox..."
restart_jottabox
