#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/stable"
BIN="$HOME/.local/bin"
mkdir -p "$BIN"

echo ">>> Instalando atualizador estável do JottaBox"
curl -fsSL "$RAW/updater/jottabox-update.sh" -o "$BIN/jottabox-update"
chmod +x "$BIN/jottabox-update"

echo ">>> Executando atualização pelo canal stable"
exec "$BIN/jottabox-update"
