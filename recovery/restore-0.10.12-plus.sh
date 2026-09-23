#!/usr/bin/env bash
set -Eeuo pipefail
BRANCH="recovery/0.10.12-plus"
REPO="jotanuior/jottabox"
API="https://api.github.com/repos/$REPO/contents"
BIN="$HOME/.local/bin"; CFG="$HOME/.config/jottabox-console"; STATE="$HOME/.local/share/jottabox"
mkdir -p "$BIN" "$CFG" "$STATE" "$HOME/Downloads/rom" "$HOME/ROMs"

get(){ curl -fsSL -H 'Accept: application/vnd.github.raw+json' -H 'Cache-Control: no-cache, no-store' "$API/$1?ref=$BRANCH" -o "$2"; }

echo ">>> Restaurando Launcher JottaBox 0.10.12+"
get recovery/launcher-0.10.12-plus.py "$CFG/launcher.py"
get recovery/jottabox-compat-0.10.12.sh "$STATE/jottabox.sh"
get scripts/jottabox-downloader.py "$CFG/downloader.py"
get scripts/jottabox-configure-input.py "$CFG/configure_input.py"
get scripts/jottabox-import-assistant.py "$CFG/import_assistant.py"
get scripts/jottabox-fullscreen-policy.py "$CFG/fullscreen_policy.py"

python3 -m py_compile "$CFG/launcher.py" "$CFG/downloader.py" "$CFG/configure_input.py" "$CFG/import_assistant.py"

cat > "$BIN/jottabox-console" <<'EOF'
#!/usr/bin/env bash
xset s off >/dev/null 2>&1 || true
xset -dpms >/dev/null 2>&1 || true
xset s noblank >/dev/null 2>&1 || true
exec /usr/bin/python3 "$HOME/.config/jottabox-console/launcher.py"
EOF

cat > "$BIN/jottabox-download-roms" <<'EOF'
#!/usr/bin/env bash
exec python3 "$HOME/.config/jottabox-console/downloader.py"
EOF

cat > "$BIN/jottabox-configure-controller" <<'EOF'
#!/usr/bin/env bash
exec python3 "$HOME/.config/jottabox-console/configure_input.py"
EOF

cat > "$BIN/jottabox-import-roms" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
SRC="${1:-$HOME/Downloads/rom}"
"$HOME/.local/share/jottabox/jottabox.sh" storage-check
python3 "$HOME/.config/jottabox-console/import_assistant.py" "$SRC"
exec "$HOME/.local/share/jottabox/jottabox.sh" import "$SRC"
EOF

for pair in  "jottabox-clean-roms clean"  "jottabox-status status"  "jottabox-storage storage"
do
  set -- $pair
  cat > "$BIN/$1" <<EOF
#!/usr/bin/env bash
exec "$HOME/.local/share/jottabox/jottabox.sh" "$2"
EOF
done

cat > "$BIN/jottabox-controller-diagnostics" <<'EOF'
#!/usr/bin/env bash
python3 - <<'PY'
import pygame
pygame.init(); pygame.joystick.init()
print("Controles:",pygame.joystick.get_count())
for i in range(pygame.joystick.get_count()):
    j=pygame.joystick.Joystick(i); j.init()
    print(i,j.get_name(),j.get_guid())
PY
EOF

cat > "$BIN/jottabox-repair-hotkey" <<'EOF'
#!/usr/bin/env bash
echo "Hotkey: SELECT + START"
echo "Use Configurar Controle para refazer o perfil se necessário."
EOF

# updater da linha estável 0.10.12
curl -fsSL -H 'Accept: application/vnd.github.raw+json'   "https://api.github.com/repos/$REPO/contents/updater/jottabox-update.sh?ref=main"   -o "$BIN/jottabox-update"

chmod +x "$BIN"/jottabox-* "$STATE/jottabox.sh" "$CFG"/*.py 2>/dev/null || true
echo "0.10.12" > "$STATE/VERSION"

mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/jottabox-console.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=JottaBox
Exec=$BIN/jottabox-console
Terminal=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

echo
echo "OK: Launcher JottaBox 0.10.12+ restaurado."
echo "Inicie com: ~/.local/bin/jottabox-console"
