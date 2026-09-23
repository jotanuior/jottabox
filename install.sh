#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
RUNTIME_ARG="${1:-}"
STATE="$HOME/.local/share/jottabox"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jottabox-console"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say(){ printf '\n>>> %s\n' "$*"; }
die(){ echo "ERRO: $*" >&2; exit 1; }

if [[ "$EUID" -eq 0 ]]; then
  die "Execute como usuário normal, não como root. O script pedirá sudo quando necessário."
fi

say "JottaBox - instalação nova"

# 1) Dependências do sistema
say "Instalando dependências"
sudo apt update
sudo apt install -y   git curl wget unzip p7zip-full rsync   python3 python3-pygame python3-evdev   xdotool zenity joystick jstest-gtk   gamemode flatpak ca-certificates

# 2) Flathub / emuladores
say "Configurando Flathub"
flatpak remote-add --if-not-exists flathub   https://flathub.org/repo/flathub.flatpakrepo

say "Instalando emuladores principais"
for app in   org.libretro.RetroArch   org.ppsspp.PPSSPP   org.DolphinEmu.dolphin-emu   net.pcsx2.PCSX2   com.valvesoftware.Steam
do
  if flatpak info "$app" >/dev/null 2>&1; then
    echo "OK: $app já instalado"
  else
    flatpak install -y flathub "$app"
  fi
done

mkdir -p "$STATE" "$BIN" "$CFG" "$HOME/ROMs" "$HOME/Downloads/rom"

# 3) Resolve seed/runtime para instalação realmente limpa.
resolve_runtime() {
  if [[ -n "$RUNTIME_ARG" && -f "$RUNTIME_ARG" ]]; then
    printf '%s' "$RUNTIME_ARG"
    return 0
  fi
  if [[ -n "${JOTTABOX_RUNTIME:-}" && -f "${JOTTABOX_RUNTIME}" ]]; then
    printf '%s' "$JOTTABOX_RUNTIME"
    return 0
  fi
  if [[ -f "$HOME/jottabox-live-runtime.tar.gz" ]]; then
    printf '%s' "$HOME/jottabox-live-runtime.tar.gz"
    return 0
  fi
  if [[ -f /opt/jottabox-live/runtime.tar.gz ]]; then
    printf '%s' /opt/jottabox-live/runtime.tar.gz
    return 0
  fi
  if [[ -d /opt/jottabox-live/runtime-home ]]; then
    printf '%s' /opt/jottabox-live/runtime-home
    return 0
  fi
  return 1
}

HAS_BASE=0
if [[ -x "$BIN/jottabox-console" && -f "$CFG/launcher.py" ]]; then
  HAS_BASE=1
  echo "Instalação JottaBox existente detectada; preservando base."
fi

if [[ "$HAS_BASE" -eq 0 ]]; then
  say "Instalando runtime base"
  SEED="$(resolve_runtime || true)"
  [[ -n "$SEED" ]] || die "Instalação limpa precisa do runtime seed. Use: bash install.sh ~/jottabox-live-runtime.tar.gz"

  mkdir -p "$TMP/seed"

  if [[ -d "$SEED" ]]; then
    rsync -a "$SEED/" "$HOME/"
    OLD_HOME=""
  else
    tar -C "$TMP/seed" -xzf "$SEED"
    [[ -d "$TMP/seed/runtime-home" ]] || die "Runtime inválido: diretório runtime-home ausente"
    rsync -a "$TMP/seed/runtime-home/" "$HOME/"
    OLD_HOME="$(cat "$TMP/seed/source-home.txt" 2>/dev/null || true)"
  fi

  # Corrige caminhos absolutos exportados de outro usuário/máquina.
  if [[ -n "${OLD_HOME:-}" && "$OLD_HOME" != "$HOME" ]]; then
    say "Adaptando runtime de $OLD_HOME para $HOME"
    while IFS= read -r -d '' f; do
      file "$f" 2>/dev/null | grep -qiE 'text|script|json|xml|python|shell' || continue
      sed -i "s#${OLD_HOME//\#/\\#}#${HOME//\#/\\#}#g" "$f" 2>/dev/null || true
    done < <(find       "$HOME/.local/bin"       "$HOME/.local/share/jottabox"       "$HOME/.config/jottabox-console"       "$HOME/.emulationstation"       "$HOME/ES-DE"       -type f -print0 2>/dev/null)
  fi
fi

chmod +x "$BIN"/jottabox-* "$BIN/gpbox" "$BIN/xbox-cloud" 2>/dev/null || true

[[ -x "$BIN/jottabox-console" ]] || die "Runtime instalado, mas ~/.local/bin/jottabox-console não foi encontrado"
[[ -f "$CFG/launcher.py" ]] || die "Runtime instalado, mas launcher.py não foi encontrado"

# 4) Atualizador oficial
say "Instalando atualizador oficial"
curl -fsSL -H 'Cache-Control: no-cache'   "$RAW/updater/jottabox-update.sh?$(date +%s%N)"   -o "$BIN/jottabox-update"
chmod +x "$BIN/jottabox-update"

# 5) Aplicar versão mais nova sem depender da versão do seed.
say "Atualizando para a versão atual"
"$BIN/jottabox-update" <<<'s' || true

# 6) Fullscreen policy
if [[ -f "$CFG/fullscreen_policy.py" ]]; then
  python3 "$CFG/fullscreen_policy.py" || true
fi

# 7) Autostart direto, sem terminal.
say "Configurando inicialização automática"
mkdir -p "$HOME/.config/autostart"

rm -f   "$HOME/.config/autostart/m720q-console.desktop"   "$HOME/.config/autostart/xbox-console.desktop"   "$HOME/.config/autostart/"*xbox*.desktop   "$HOME/.config/autostart/"*cloud*.desktop 2>/dev/null || true

cat > "$HOME/.config/autostart/jottabox-console.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=JottaBox
Comment=Interface de console JottaBox
Exec=$BIN/jottabox-console
Terminal=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

# 8) Garantir pastas de biblioteca.
mkdir -p "$HOME/ROMs"/{nes,snes,megadrive,sega32x,segacd,saturn,mastersystem,gamegear,gb,gbc,gba,nds,n64,psx,ps2,psp,gc,wii,dreamcast,pcengine,pcenginecd,atari2600,atari5200,atari7800,atarilynx,ngp,ngpc,wonderswan,wonderswancolor,neogeo,arcade,_revisar,_arquivo}
mkdir -p "$HOME/Downloads/rom"

say "Validação"
echo "Launcher: $BIN/jottabox-console"
echo "Versão:   $(cat "$STATE/VERSION" 2>/dev/null || echo desconhecida)"
echo "ROMs:     $HOME/ROMs"
echo
echo "Instalação concluída."
echo "Para iniciar agora:"
echo "  $BIN/jottabox-console"
echo
echo "Para usar no próximo login, o autostart já está configurado."
