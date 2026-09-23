#!/usr/bin/env bash
set -Eeuo pipefail

REPO_RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
STATE_DIR="$HOME/.local/share/jottabox"
ENGINE="$STATE_DIR/jottabox.sh"
BACKUP_DIR="$STATE_DIR/backups"
TMP="$(mktemp -d)"

cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT

say(){ printf '\n>>> %s\n' "$*"; }
die(){ echo "ERRO: $*" >&2; exit 1; }

mkdir -p "$STATE_DIR" "$BACKUP_DIR"

say "Consultando versão disponível"
curl -fsSL "$REPO_RAW/manifest.json" -o "$TMP/manifest.json"

REMOTE_VERSION="$(
python3 - "$TMP/manifest.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1],encoding="utf-8"))["version"])
PY
)"

LOCAL_VERSION="0.0.0"
if [[ -x "$ENGINE" ]]; then
  LOCAL_VERSION="$("$ENGINE" version 2>/dev/null || true)"
  [[ -n "$LOCAL_VERSION" ]] || LOCAL_VERSION="$(
    grep -m1 '^VERSION=' "$ENGINE" 2>/dev/null |
    cut -d= -f2- | tr -d '"'
  )"
  [[ -n "$LOCAL_VERSION" ]] || LOCAL_VERSION="0.0.0"
fi

echo "Instalada:   $LOCAL_VERSION"
echo "Disponível: $REMOTE_VERSION"

if [[ "$LOCAL_VERSION" == "$REMOTE_VERSION" ]]; then
  echo "JottaBox já está atualizado."
  exit 0
fi

say "Baixando JottaBox $REMOTE_VERSION"
curl -fsSL "$REPO_RAW/jottabox.sh" -o "$TMP/jottabox.sh"
chmod +x "$TMP/jottabox.sh"

bash -n "$TMP/jottabox.sh" || die "A versão baixada falhou na validação."

if [[ -f "$ENGINE" ]]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$BACKUP_DIR/$stamp"
  cp -a "$ENGINE" "$BACKUP_DIR/$stamp/jottabox.sh"
  echo "$LOCAL_VERSION" > "$BACKUP_DIR/$stamp/VERSION"
fi

say "Instalando atualização"
install -m 755 "$TMP/jottabox.sh" "$ENGINE.new"
mv -f "$ENGINE.new" "$ENGINE"

"$ENGINE" repair-wrappers

echo
echo "Atualização concluída: $REMOTE_VERSION"
