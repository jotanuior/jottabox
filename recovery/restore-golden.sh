#!/usr/bin/env bash
set -Eeuo pipefail

ARCHIVE="${1:-}"
[[ -n "$ARCHIVE" && -f "$ARCHIVE" ]] || {
  echo "Uso: bash restore-golden.sh /caminho/jottabox-runtime.tar.gz"
  exit 2
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo ">>> Extraindo snapshot da máquina boa"
tar -C "$TMP" -xzf "$ARCHIVE"
[[ -d "$TMP/runtime-home" ]] || { echo "ERRO: runtime-home ausente"; exit 1; }

OLD_HOME="$(cat "$TMP/source-home.txt" 2>/dev/null || true)"

echo ">>> Removendo somente a base JottaBox atual"
rm -rf "$HOME/.config/jottabox-console"
rm -rf "$HOME/.local/share/jottabox"
rm -rf "$HOME/.emulationstation"
rm -rf "$HOME/ES-DE"
rm -f "$HOME/.local/bin"/jottabox-* "$HOME/.local/bin/gpbox" "$HOME/.local/bin/xbox-cloud" 2>/dev/null || true
rm -f "$HOME/.config/autostart"/jottabox*.desktop 2>/dev/null || true

echo ">>> Restaurando base validada"
rsync -a "$TMP/runtime-home/" "$HOME/"

if [[ -n "$OLD_HOME" && "$OLD_HOME" != "$HOME" ]]; then
  echo ">>> Adaptando caminhos: $OLD_HOME -> $HOME"
  while IFS= read -r -d '' f; do
    file "$f" 2>/dev/null | grep -qiE 'text|script|json|xml|python|shell' || continue
    sed -i "s#${OLD_HOME//\#/\\#}#${HOME//\#/\\#}#g" "$f" 2>/dev/null || true
  done < <(find     "$HOME/.local/bin"     "$HOME/.local/share/jottabox"     "$HOME/.config/jottabox-console"     "$HOME/.emulationstation"     "$HOME/ES-DE"     -type f -print0 2>/dev/null)
fi

chmod +x "$HOME/.local/bin"/jottabox-* "$HOME/.local/bin/gpbox" "$HOME/.local/bin/xbox-cloud" 2>/dev/null || true

mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/jottabox-console.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=JottaBox
Exec=$HOME/.local/bin/jottabox-console
Terminal=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

echo
echo ">>> Validando"
test -x "$HOME/.local/bin/jottabox-console"
test -f "$HOME/.config/jottabox-console/launcher.py"

echo "OK: base da máquina boa restaurada."
echo "ROMs e Downloads não foram alterados."
