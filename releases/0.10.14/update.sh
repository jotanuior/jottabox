#!/usr/bin/env bash
set -Eeuo pipefail

VERSION_NEW="0.10.14"
VERSION_OLD="0.10.13"

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/stable"

STATE="$HOME/.local/share/jottabox"
CFG="$HOME/.config/jottabox-console"
BIN="$HOME/.local/bin"

BACKUP="$STATE/backups/$VERSION_NEW-$(date +%Y%m%d-%H%M%S)"
TMP="$(mktemp -d)"
COMMITTED=0

trap 'rm -rf "$TMP"' EXIT

mkdir -p \
  "$STATE" \
  "$CFG" \
  "$BIN" \
  "$BACKUP"

rollback_on_error() {
    [[ "$COMMITTED" -eq 0 ]] || return 0

    echo
    echo "ERRO: atualização não concluída. Restaurando configuração anterior..."

    if [[ -f "$BACKUP/configure_input.py" ]]; then
        cp -a "$BACKUP/configure_input.py" "$CFG/configure_input.py"
    fi

    if [[ -f "$BACKUP/VERSION" ]]; then
        cp -a "$BACKUP/VERSION" "$STATE/VERSION"
    fi
}

trap rollback_on_error ERR INT TERM

echo ">>> Atualizando JottaBox para $VERSION_NEW"

if [[ -f "$CFG/configure_input.py" ]]; then
    cp -a \
      "$CFG/configure_input.py" \
      "$BACKUP/configure_input.py"
fi

if [[ -f "$STATE/VERSION" ]]; then
    cp -a \
      "$STATE/VERSION" \
      "$BACKUP/VERSION"
fi

echo ">>> Baixando novo configurador de controle"

curl -fsSL \
  "$RAW/scripts/jottabox-configure-input.py" \
  -o "$TMP/configure_input.py"

echo ">>> Validando Python"

python3 -m py_compile \
  "$TMP/configure_input.py"

echo ">>> Instalando configurador"

install -m 0755 \
  "$TMP/configure_input.py" \
  "$CFG/configure_input.py"

echo "$VERSION_NEW" > "$STATE/VERSION"

python3 -m py_compile \
  "$CFG/configure_input.py"

[[ "$(cat "$STATE/VERSION")" == "$VERSION_NEW" ]]

COMMITTED=1
trap - ERR INT TERM

echo
echo "OK: JottaBox $VERSION_NEW instalado."
echo "Novo editor visual de controles disponível."
echo "Backup: $BACKUP"
