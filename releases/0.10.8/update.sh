#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
BIN="$HOME/.local/bin"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.8-$(date +%Y%m%d-%H%M%S)"
LAUNCHER="$CFG/launcher.py"

mkdir -p "$CFG" "$BIN" "$BACKUP"

echo ">>> Backup do launcher"
[[ -f "$LAUNCHER" ]] && cp -a "$LAUNCHER" "$BACKUP/launcher.py" || true

echo ">>> Aplicando padrão de console interno"
curl -fsSL "$RAW/scripts/jottabox-internal-console-policy.py" -o "$CFG/internal_console_policy.py"
python3 -m py_compile "$CFG/internal_console_policy.py"
python3 "$CFG/internal_console_policy.py"
python3 -m py_compile "$LAUNCHER"

echo ">>> Instalando auditoria"
curl -fsSL "$RAW/scripts/jottabox-terminal-audit.sh" -o "$BIN/jottabox-terminal-audit"
chmod +x "$BIN/jottabox-terminal-audit"

echo ">>> Auditando instalação"
if ! "$BIN/jottabox-terminal-audit"; then
  echo "AVISO: há referência antiga a terminal externo em algum componente."
  echo "O launcher principal já foi protegido para as ferramentas administrativas."
fi

echo "0.10.8" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.8 instalado"
echo "Ferramentas CLI agora usam o console interno do JottaBox."
echo "Backup: $BACKUP"
