#!/usr/bin/env bash
set -Eeuo pipefail

OUT="${1:-$HOME/jottabox-live-runtime.tar.gz}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SRC_HOME="$HOME"
DST="$TMP/runtime-home"
mkdir -p "$DST"

copy_item() {
  local src="$1" rel="$2"
  [[ -e "$src" ]] || return 0

  if [[ -d "$src" ]]; then
    mkdir -p "$DST/$rel"
    rsync -a --copy-links "$src/" "$DST/$rel/"
  else
    mkdir -p "$DST/$(dirname "$rel")"
    rsync -a --copy-links "$src" "$DST/$rel"
  fi
}

echo ">>> Exportando runtime JottaBox de $SRC_HOME"

copy_item "$HOME/.local/share/jottabox" ".local/share/jottabox"
copy_item "$HOME/.config/jottabox-console" ".config/jottabox-console"
copy_item "$HOME/.emulationstation" ".emulationstation"
copy_item "$HOME/ES-DE" "ES-DE"

mkdir -p "$DST/.local/bin"
while IFS= read -r -d '' f; do
  cp -aL "$f" "$DST/.local/bin/$(basename "$f")"
done < <(find "$HOME/.local/bin" -maxdepth 1 -type f \( -name 'jottabox-*' -o -name 'gpbox' -o -name 'xbox-cloud' \) -print0 2>/dev/null)

# Configurações e cores que já foram validados.
copy_item "$HOME/.var/app/org.libretro.RetroArch/config/retroarch" ".var/app/org.libretro.RetroArch/config/retroarch"
copy_item "$HOME/.var/app/org.ppsspp.PPSSPP/config" ".var/app/org.ppsspp.PPSSPP/config"

# ES-DE AppImage, se estiver no diretório comum.
mkdir -p "$DST/Applications"
for f in "$HOME"/Applications/ES-DE*.AppImage "$HOME"/Applications/es-de*.AppImage; do
  [[ -f "$f" ]] && cp -a "$f" "$DST/Applications/"
done

# Nunca carregar conteúdo pessoal/jogos para a ISO.
rm -rf   "$DST/ROMs"   "$DST/Downloads"   "$DST/.local/share/jottabox/backups"   "$DST/.local/share/jottabox/logs"   "$DST/.config/google-chrome"   "$DST/.config/microsoft-edge"   "$DST/.ssh" 2>/dev/null || true

# Ajustes exclusivos da versão Live.
LIVE_LAUNCHER="$DST/.config/jottabox-console/launcher.py"

if [[ -f "$LIVE_LAUNCHER" ]]; then
python3 - "$LIVE_LAUNCHER" <<'PYLIVE'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

s = s.replace(
    '"organize":load_img("library_organize.png"),',
    '"organize":load_img("library_organize.png"),\n "external":load_img("library_import.png"),\n "romstorage":load_img("library_import.png"),'
)

s = s.replace(
    '("organize",os.path.join(BIN,"jottabox-clean-roms")),\n ("back","__back__"),',
    '("organize",os.path.join(BIN,"jottabox-clean-roms")),\n ("external","/usr/local/bin/jottabox-external-roms"),\n ("romstorage","/usr/local/bin/jottabox-rom-storage"),\n ("back","__back__"),'
)

s = s.replace(
    '"back":("VOLTAR","Retornar à Home","←"),',
    '"external":("FONTES EXTERNAS","Usar ROMs existentes sem copiar","▣"),\n "romstorage":("ARMAZENAMENTO DE ROMS","Salvar ROMs permanentemente em HD/SSD","▣"),\n "back":("VOLTAR","Retornar à Home","←"),'
)

# No Live, não bloquear o loop do Pygame enquanto Steam e outros apps ficam abertos.
old_external = """        else:
            subprocess.run(run,shell=True)

    except Exception:
        pass
"""

new_external = """        else:
            proc = subprocess.Popen(run, shell=True)

            while proc.poll() is None:
                pygame.event.pump()
                time.sleep(.15)

    except Exception:
        pass
"""

if old_external not in s:
    raise SystemExit("ERRO: bloco externo do launcher não encontrado")

s = s.replace(old_external, new_external, 1)

p.write_text(s)
PYLIVE

XCLOUD="$DST/.local/bin/xbox-cloud"

if [[ -f "$XCLOUD" ]]; then
cat > "$XCLOUD" <<'SHXCLOUD'
#!/usr/bin/env bash
set -Eeuo pipefail

EDGE="$(command -v microsoft-edge-stable || command -v microsoft-edge || true)"

[[ -n "$EDGE" ]] || {
    zenity --error --text="Microsoft Edge não encontrado."
    exit 1
}

PROFILE="$HOME/.config/jottabox-edge-xcloud"
MARK="$PROFILE/.better-xcloud-first-run"

mkdir -p "$PROFILE"

XBOX_URL="https://www.xbox.com/play"
BETTER_FILE="/opt/jottabox-live/better-xcloud.user.js"

COMMON=(
    --user-data-dir="$PROFILE"
    --no-first-run
    --disable-session-crashed-bubble
    --disable-background-mode
    --disable-features=msEdgeStartupBoost
)

# Primeiro uso: abre o userscript para o Tampermonkey instalar.
if [[ ! -f "$MARK" && -f "$BETTER_FILE" ]]; then
    "$EDGE" \
        "${COMMON[@]}" \
        "file://$BETTER_FILE" &

    zenity \
        --info \
        --title="Better xCloud" \
        --width=520 \
        --text="Primeiro uso do XCloud.

O Tampermonkey abrirá a tela de instalação do Better xCloud.

Clique em Instalar.

Depois feche essa janela do Edge e pressione OK aqui."

    touch "$MARK"
fi

exec "$EDGE" \
    "${COMMON[@]}" \
    --start-fullscreen \
    --kiosk \
    --app="$XBOX_URL"
SHXCLOUD

chmod +x "$XCLOUD"
fi

fi

printf '%s\n' "$SRC_HOME" > "$TMP/source-home.txt"
printf '%s\n' "$(cat "$HOME/.local/share/jottabox/VERSION" 2>/dev/null || echo unknown)" > "$TMP/jottabox-version.txt"

tar -C "$TMP" -czf "$OUT" runtime-home source-home.txt jottabox-version.txt

echo
echo "OK: $OUT"
du -h "$OUT"
echo "ROMs, BIOS, downloads, SSH e dados do navegador não foram incluídos."
