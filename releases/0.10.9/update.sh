#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.9-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BIN" "$CFG" "$BACKUP"

cat > "$BIN/jottabox-launch-psp" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
ROM="${1:?Informe o jogo de PSP}"
exec flatpak run org.ppsspp.PPSSPP "$ROM"
EOF
chmod +x "$BIN/jottabox-launch-psp"

curl -fsSL "$RAW/scripts/jottabox-fix-psp-esde-allpaths.py" -o "$CFG/fix_psp_esde_allpaths.py"
python3 -m py_compile "$CFG/fix_psp_esde_allpaths.py"
python3 "$CFG/fix_psp_esde_allpaths.py"

echo "0.10.9" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.9 instalado"
echo "PSP agora aponta para jottabox-launch-psp em todos os diretórios compatíveis do ES-DE."
echo "Reinicie o ES-DE/JottaBox para recarregar a configuração."
