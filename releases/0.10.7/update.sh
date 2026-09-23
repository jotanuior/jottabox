#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.7-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$CFG" "$BACKUP"

echo ">>> Verificando PPSSPP"
if ! flatpak info org.ppsspp.PPSSPP >/dev/null 2>&1; then
  echo "ERRO: PPSSPP Flatpak não está instalado."
  exit 1
fi

echo ">>> Corrigindo PSP no ES-DE"
curl -fsSL "$RAW/scripts/jottabox-fix-psp-esde.py" -o "$CFG/fix_psp_esde.py"
python3 -m py_compile "$CFG/fix_psp_esde.py"
python3 "$CFG/fix_psp_esde.py"

cat > "$HOME/.local/bin/jottabox-launch-psp" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
ROM="${1:?Informe o arquivo do jogo}"
exec flatpak run org.ppsspp.PPSSPP "$ROM"
EOF
chmod +x "$HOME/.local/bin/jottabox-launch-psp"

echo "0.10.7" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.7 instalado"
echo "PSP agora abre no PPSSPP standalone."
echo "O RetroArch não será usado para jogos de PSP."
