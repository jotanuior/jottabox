#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.12-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BIN" "$CFG" "$BACKUP"

echo ">>> Aplicando fullscreen padrão"
curl -fsSL "$RAW/scripts/jottabox-fullscreen-policy.py" -o "$CFG/fullscreen_policy.py"
python3 -m py_compile "$CFG/fullscreen_policy.py"
python3 "$CFG/fullscreen_policy.py"

echo ">>> Atualizando launcher PSP"
cat > "$BIN/jottabox-launch-psp" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
ROM="${1:?Informe o jogo de PSP}"

# Reaplica a política antes de abrir, caso o emulador tenha alterado a preferência.
python3 "$HOME/.config/jottabox-console/fullscreen_policy.py" >/dev/null 2>&1 || true

exec flatpak run org.ppsspp.PPSSPP --fullscreen "$ROM"
EOF
chmod +x "$BIN/jottabox-launch-psp"

echo ">>> Criando wrappers fullscreen"
cat > "$BIN/jottabox-launch-retroarch" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
python3 "$HOME/.config/jottabox-console/fullscreen_policy.py" >/dev/null 2>&1 || true
exec flatpak run org.libretro.RetroArch --fullscreen "$@"
EOF
chmod +x "$BIN/jottabox-launch-retroarch"

cat > "$BIN/jottabox-launch-dolphin" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
python3 "$HOME/.config/jottabox-console/fullscreen_policy.py" >/dev/null 2>&1 || true
exec flatpak run org.DolphinEmu.dolphin-emu -b -e "$1"
EOF
chmod +x "$BIN/jottabox-launch-dolphin"

cat > "$BIN/jottabox-launch-pcsx2" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
python3 "$HOME/.config/jottabox-console/fullscreen_policy.py" >/dev/null 2>&1 || true
exec flatpak run net.pcsx2.PCSX2 -fullscreen "$1"
EOF
chmod +x "$BIN/jottabox-launch-pcsx2"

echo "0.10.12" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.12 instalado"
echo "Fullscreen forçado para RetroArch, PPSSPP, Dolphin e PCSX2."
echo "Backup/política: $BACKUP"
