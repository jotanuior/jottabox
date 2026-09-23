#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.10-$(date +%Y%m%d-%H%M%S)"
LAUNCHER="$CFG/launcher.py"

mkdir -p "$CFG" "$BACKUP"

echo ">>> Backup do launcher"
cp -a "$LAUNCHER" "$BACKUP/launcher.py"

echo ">>> Corrigindo telas gráficas internas"
curl -fsSL "$RAW/scripts/jottabox-native-gui-policy.py" -o "$CFG/native_gui_policy.py"
python3 -m py_compile "$CFG/native_gui_policy.py"
python3 "$CFG/native_gui_policy.py"
python3 -m py_compile "$LAUNCHER"

echo "0.10.10" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.10 instalado"
echo "Configurar controle agora abre direto como tela gráfica do JottaBox."
echo "Nenhum terminal deve aparecer nesse fluxo."
echo "Backup: $BACKUP"
