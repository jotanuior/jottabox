#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
STATE_DIR="$HOME/.local/share/jottabox"
BIN_DIR="$HOME/.local/bin"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$STATE_DIR" "$BIN_DIR"

fresh_url() {
  printf '%s/%s?cb=%s' "$RAW" "$1" "$(date +%s%N)"
}
get_fresh() {
  curl -fsSL     -H 'Cache-Control: no-cache, no-store, max-age=0'     -H 'Pragma: no-cache'     "$(fresh_url "$1")" -o "$2"
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

get_fresh "manifest.json" "$TMP/manifest.json"

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

LOCAL="$(cat "$STATE_DIR/VERSION" 2>/dev/null || true)"
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

get_fresh "$SCRIPT" "$TMP/update.sh"
bash -n "$TMP/update.sh"
chmod +x "$TMP/update.sh"

"$TMP/update.sh"

# A release só é considerada instalada se ela própria terminar sem erro.
INSTALLED="$(cat "$STATE_DIR/VERSION" 2>/dev/null || true)"
if [[ "$INSTALLED" != "$REMOTE" ]]; then
  echo "ERRO: atualização executou, mas VERSION ficou em '$INSTALLED' em vez de '$REMOTE'."
  exit 1
fi

echo
echo "Atualização concluída. Reiniciando a interface do JottaBox..."
restart_jottabox
