#!/usr/bin/env bash
set -Eeuo pipefail

REPO="jotanuior/jottabox"
API="https://api.github.com/repos/$REPO/contents"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
APPS="$HOME/Applications"
ESDATA="$HOME/ES-DE"
VERSION="0.11.0"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say(){ printf '\n>>> %s\n' "$*"; }
die(){ echo "ERRO: $*" >&2; exit 1; }

[[ "$EUID" -ne 0 ]] || die "Execute como usuário normal, não como root."

api_file() {
  local path="$1" dest="$2"
  curl -fsSL     -H 'Accept: application/vnd.github.raw+json'     -H 'Cache-Control: no-cache, no-store, max-age=0'     "https://api.github.com/repos/$REPO/contents/$path?ref=main"     -o "$dest"
}

say "JottaBox $VERSION - instalação limpa/autocontida"

say "Instalando dependências"
sudo apt update
sudo apt install -y   git curl wget unzip p7zip-full rsync file   python3 python3-pygame python3-evdev   xdotool zenity joystick jstest-gtk   gamemode flatpak ca-certificates

say "Configurando Flathub (system)"
sudo flatpak --system remote-add --if-not-exists flathub   https://flathub.org/repo/flathub.flatpakrepo

say "Instalando emuladores"
for app in   org.libretro.RetroArch   org.ppsspp.PPSSPP   org.DolphinEmu.dolphin-emu   net.pcsx2.PCSX2   com.valvesoftware.Steam
do
  if flatpak --system info "$app" >/dev/null 2>&1; then
    echo "OK: $app"
  else
    sudo flatpak --system install -y flathub "$app"
  fi
done

say "Criando estrutura"
mkdir -p "$BIN" "$CFG" "$STATE" "$APPS" "$ESDATA/custom_systems" "$HOME/Downloads/rom"
mkdir -p "$HOME/ROMs"/{nes,snes,megadrive,sega32x,segacd,saturn,mastersystem,gamegear,gb,gbc,gba,nds,n64,psx,ps2,psp,gc,wii,dreamcast,pcengine,pcenginecd,atari2600,atari5200,atari7800,atarilynx,ngp,ngpc,wonderswan,wonderswancolor,neogeo,arcade,_revisar,_arquivo}

say "Baixando base oficial do JottaBox"
api_file base/launcher.py "$CFG/launcher.py"
api_file base/console_runner.py "$CFG/console_runner.py"
api_file base/jottabox.sh "$STATE/jottabox.sh"
api_file base/es_systems.xml "$ESDATA/custom_systems/es_systems.xml"

api_file scripts/jottabox-downloader.py "$CFG/downloader.py"
api_file scripts/jottabox-configure-input.py "$CFG/configure_input.py"
api_file scripts/jottabox-import-assistant.py "$CFG/import_assistant.py"
api_file scripts/jottabox-import-progress.py "$CFG/import_progress.py"
api_file scripts/jottabox-fullscreen-policy.py "$CFG/fullscreen_policy.py"

python3 -m py_compile   "$CFG/launcher.py"   "$CFG/console_runner.py"   "$CFG/downloader.py"   "$CFG/configure_input.py"   "$CFG/import_assistant.py"   "$CFG/import_progress.py"   "$CFG/fullscreen_policy.py"

chmod +x "$STATE/jottabox.sh" "$CFG"/*.py

say "Instalando ES-DE"
curl -fsSL   -H 'Accept: application/vnd.github.raw+json'   https://api.github.com/repos/UzuCore/es-de/contents/latest_release.json   -o "$TMP/esde-release.json"

readarray -t ESINFO < <(python3 - "$TMP/esde-release.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
for p in d["stable"]["packages"]:
    if p["name"]=="LinuxAppImage":
        print(p["url"])
        print(p["md5"])
        print(d["stable"]["version"])
        break
else:
    raise SystemExit("LinuxAppImage não encontrado")
PY
)
ES_URL="${ESINFO[0]}"
ES_MD5="${ESINFO[1]}"
ES_VER="${ESINFO[2]}"
curl -fL --retry 3 "$ES_URL" -o "$APPS/ES-DE_x64.AppImage"
echo "$ES_MD5  $APPS/ES-DE_x64.AppImage" | md5sum -c -
chmod +x "$APPS/ES-DE_x64.AppImage"
echo "ES-DE $ES_VER instalado."

say "Criando wrappers"

cat > "$BIN/jottabox-console" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
xset s off >/dev/null 2>&1 || true
xset -dpms >/dev/null 2>&1 || true
xset s noblank >/dev/null 2>&1 || true
exec /usr/bin/python3 "$HOME/.config/jottabox-console/launcher.py"
EOF

cat > "$BIN/gpbox" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
export ESDE_APPDATA_DIR="$HOME/ES-DE"
exec "$HOME/Applications/ES-DE_x64.AppImage"
EOF

cat > "$BIN/xbox-cloud" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
URL="https://www.xbox.com/play"
for b in microsoft-edge-stable microsoft-edge google-chrome-stable google-chrome chromium chromium-browser; do
  if command -v "$b" >/dev/null 2>&1; then
    exec "$b" --start-fullscreen --app="$URL" --user-data-dir="$HOME/.config/jottabox-edge-xcloud"
  fi
done
exec xdg-open "$URL"
EOF

cat > "$BIN/jottabox-import-roms" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
SRC="${1:-$HOME/Downloads/rom}"
ENGINE="$HOME/.local/share/jottabox/jottabox.sh"
"$ENGINE" storage-check
python3 "$HOME/.config/jottabox-console/import_assistant.py" "$SRC"
exec python3 "$HOME/.config/jottabox-console/import_progress.py" "$SRC"
EOF

cat > "$BIN/jottabox-download-roms" <<'EOF'
#!/usr/bin/env bash
exec python3 "$HOME/.config/jottabox-console/downloader.py"
EOF

cat > "$BIN/jottabox-configure-controller" <<'EOF'
#!/usr/bin/env bash
exec python3 "$HOME/.config/jottabox-console/configure_input.py"
EOF

cat > "$BIN/jottabox-clean-roms" <<'EOF'
#!/usr/bin/env bash
exec "$HOME/.local/share/jottabox/jottabox.sh" clean
EOF

cat > "$BIN/jottabox-status" <<'EOF'
#!/usr/bin/env bash
exec "$HOME/.local/share/jottabox/jottabox.sh" status
EOF

cat > "$BIN/jottabox-storage" <<'EOF'
#!/usr/bin/env bash
exec "$HOME/.local/share/jottabox/jottabox.sh" storage
EOF

cat > "$BIN/jottabox-controller-diagnostics" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
echo "=== CONTROLES ==="
ls -l /dev/input/js* 2>/dev/null || echo "Nenhum /dev/input/js encontrado"
echo
echo "=== SDL/PYGAME ==="
python3 - <<'PY'
import pygame
pygame.init(); pygame.joystick.init()
print("Quantidade:",pygame.joystick.get_count())
for i in range(pygame.joystick.get_count()):
    j=pygame.joystick.Joystick(i); j.init()
    print(i,j.get_name(),j.get_guid())
PY
EOF

cat > "$BIN/jottabox-repair-hotkey" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
echo "Hotkey global será recriado automaticamente na próxima inicialização."
echo "Configurações de controle ficam em ~/.config/jottabox-console/controllers/"
EOF

cat > "$BIN/jottabox-launch-psp" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
ROM="${1:?Informe o jogo}"
python3 "$HOME/.config/jottabox-console/fullscreen_policy.py" >/dev/null 2>&1 || true
exec flatpak run org.ppsspp.PPSSPP --fullscreen "$ROM"
EOF

cat > "$BIN/jottabox-launch-pcsx2" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
ROM="${1:?Informe o jogo}"
python3 "$HOME/.config/jottabox-console/fullscreen_policy.py" >/dev/null 2>&1 || true
exec flatpak run net.pcsx2.PCSX2 -fullscreen "$ROM"
EOF

cat > "$BIN/jottabox-launch-dolphin" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
ROM="${1:?Informe o jogo}"
python3 "$HOME/.config/jottabox-console/fullscreen_policy.py" >/dev/null 2>&1 || true
exec flatpak run org.DolphinEmu.dolphin-emu -b -e "$ROM"
EOF

cat > "$BIN/jottabox-launch-retroarch" <<'EOF'
#!/usr/bin/env bash
exec flatpak run org.libretro.RetroArch --fullscreen "$@"
EOF

api_file updater/jottabox-update.sh "$BIN/jottabox-update"
chmod +x "$BIN"/jottabox-* "$BIN/gpbox" "$BIN/xbox-cloud"

say "Aplicando fullscreen"
python3 "$CFG/fullscreen_policy.py" || true

say "Configurando autostart sem terminal"
mkdir -p "$HOME/.config/autostart"
rm -f "$HOME/.config/autostart"/jottabox*.desktop       "$HOME/.config/autostart"/m720q-console.desktop       "$HOME/.config/autostart"/xbox-console.desktop       "$HOME/.config/autostart"/*xbox*.desktop       "$HOME/.config/autostart"/*cloud*.desktop 2>/dev/null || true

cat > "$HOME/.config/autostart/jottabox-console.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=JottaBox
Exec=$BIN/jottabox-console
Terminal=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/jottabox-console.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=JottaBox
Exec=$BIN/jottabox-console
Terminal=false
Categories=Game;
EOF

echo "$VERSION" > "$STATE/VERSION"

say "Validação"
for f in   "$BIN/jottabox-console"   "$BIN/jottabox-import-roms"   "$BIN/jottabox-download-roms"   "$BIN/jottabox-configure-controller"   "$BIN/gpbox"   "$CFG/launcher.py"   "$CFG/downloader.py"   "$STATE/jottabox.sh"   "$APPS/ES-DE_x64.AppImage"
do
  [[ -e "$f" ]] || die "Faltou: $f"
done

echo
echo "===================================================="
echo " JottaBox $VERSION instalado com base limpa."
echo "===================================================="
echo
echo "Iniciar agora:"
echo "  ~/.local/bin/jottabox-console"
echo
echo "ROMs:"
echo "  ~/ROMs"
echo
echo "Downloads:"
echo "  ~/Downloads/rom"
