#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/stable"
CHANNEL_FILE="channels/stable.json"
STATE_DIR="$HOME/.local/share/jottabox"
BIN_DIR="$HOME/.local/bin"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$STATE_DIR" "$BIN_DIR"

restart_jottabox() {
  local launcher="$BIN_DIR/jottabox-console"
  [[ -x "$launcher" ]] || return 0

  setsid -f bash -lc "
    sleep 1.5
    pkill -f '[j]ottabox-console' 2>/dev/null || true
    sleep 1
    exec '$launcher'
  " >"$HOME/.local/share/jottabox/restart.log" 2>&1 || true
}

curl -fsSL "$RAW/$CHANNEL_FILE" -o "$TMP/channel.json"

REMOTE="$(python3 - "$TMP/channel.json" <<'PY'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8"))
print(m["version"])
PY
)"

SCRIPT="$(python3 - "$TMP/channel.json" <<'PY'
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

echo "Canal:       stable"
echo "Instalada:   $LOCAL"
echo "Disponível:  $REMOTE"

if [[ "$LOCAL" == "$REMOTE" ]]; then
  echo "JottaBox já está atualizado."
  exit 0
fi

# Nunca fazer downgrade automático/acidental.
if [[ "$LOCAL" != "legado" ]]; then
  cmp="$(python3 - "$LOCAL" "$REMOTE" <<'PY'
import re,sys
def v(s):
    nums=[int(x) for x in re.findall(r'\d+', s)]
    return tuple(nums + [0] * (3-len(nums)))
a,b=v(sys.argv[1]),v(sys.argv[2])
print(1 if a>b else 0)
PY
)"
  if [[ "$cmp" == "1" ]]; then
    echo "A versão instalada é mais nova que o canal stable."
    echo "Nenhum downgrade será realizado."
    exit 0
  fi
fi

echo
echo "Novidades:"
python3 - "$TMP/channel.json" <<'PY'
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

echo
echo "Atualização concluída. Reiniciando a interface do JottaBox..."
restart_jottabox
