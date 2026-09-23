#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.11-$(date +%Y%m%d-%H%M%S)"
LAUNCHER="$CFG/launcher.py"

mkdir -p "$BIN" "$CFG" "$BACKUP"

echo ">>> Backup"
[[ -f "$LAUNCHER" ]] && cp -a "$LAUNCHER" "$BACKUP/launcher.py" || true
[[ -f "$BIN/jottabox-launch-psp" ]] && cp -a "$BIN/jottabox-launch-psp" "$BACKUP/" || true

echo ">>> Corrigindo telas gráficas sem expor terminal"
curl -fsSL "$RAW/scripts/jottabox-fix-native-gui-no-iconify.py" -o "$CFG/fix_native_gui_no_iconify.py"
python3 -m py_compile "$CFG/fix_native_gui_no_iconify.py"
python3 "$CFG/fix_native_gui_no_iconify.py"
python3 -m py_compile "$LAUNCHER"

echo ">>> Instalando launcher PSP"
cat > "$BIN/jottabox-launch-psp" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
ROM="${1:?Informe o jogo de PSP}"
exec flatpak run org.ppsspp.PPSSPP "$ROM"
EOF
chmod +x "$BIN/jottabox-launch-psp"

echo ">>> Corrigindo ES-DE PSP em todos os caminhos"
curl -fsSL "$RAW/scripts/jottabox-fix-psp-cumulative.py" -o "$CFG/fix_psp_cumulative.py"
python3 -m py_compile "$CFG/fix_psp_cumulative.py"
python3 "$CFG/fix_psp_cumulative.py"

echo ">>> Validando"
grep -q 'jottabox-launch-psp' "$HOME/ES-DE/custom_systems/es_systems.xml"
! grep -q 'pygame.display.iconify()' <(sed -n '/native_name in native_gui/,+12p' "$LAUNCHER")

echo "0.10.11" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.11 instalado"
echo "1) Configurar Controle/Downloader não expõem mais o terminal."
echo "2) PSP usa PPSSPP standalone via custom_systems real do ES-DE."
echo "3) Esta atualização é cumulativa e independe das versões 0.10.8/0.10.9/0.10.10."
echo "Backup: $BACKUP"
