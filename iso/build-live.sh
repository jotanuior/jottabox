#!/usr/bin/env bash
set -Eeuo pipefail

BASE_ISO="${1:-}"
RUNTIME="${2:-}"
LIVE_VERSION="$(cat "$ROOT/LIVE_VERSION" 2>/dev/null || echo 0.1.1)"
OUTPUT="${3:-$PWD/JottaBox-Live-${LIVE_VERSION}.iso}"

[[ -f "$BASE_ISO" ]] || { echo "Uso: sudo $0 linuxmint.iso jottabox-live-runtime.tar.gz [saida.iso]"; exit 2; }
[[ -f "$RUNTIME" ]] || { echo "Runtime não encontrado: $RUNTIME"; exit 2; }
[[ "$EUID" -eq 0 ]] || { echo "Execute com sudo."; exit 2; }

for c in xorriso unsquashfs mksquashfs rsync tar; do
  command -v "$c" >/dev/null 2>&1 || {
    echo "Falta: $c"
    echo "Instale: apt install xorriso squashfs-tools rsync"
    exit 1
  }
done

ROOT="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d /tmp/jottabox-live.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/extract" "$WORK/rootfs" "$WORK/runtime"

echo ">>> Extraindo filesystem.squashfs"
xorriso -osirrox on -indev "$BASE_ISO"   -extract /casper/filesystem.squashfs "$WORK/filesystem.squashfs" >/dev/null 2>&1

echo ">>> Abrindo SquashFS"
unsquashfs -d "$WORK/rootfs" "$WORK/filesystem.squashfs" >/dev/null

echo ">>> Aplicando overlay JottaBox Live"
rsync -a "$ROOT/rootfs-overlay/" "$WORK/rootfs/"

echo ">>> Instalando dependencias do JottaBox no Live"

cp -L /etc/resolv.conf "$WORK/rootfs/etc/resolv.conf"

chroot "$WORK/rootfs" /bin/bash -c '
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends python3-pygame rsync
    apt-get clean
    rm -rf /var/lib/apt/lists/*
'

echo ">>> Incorporando runtime JottaBox"
tar -C "$WORK/runtime" -xzf "$RUNTIME"
mkdir -p "$WORK/rootfs/opt/jottabox-live"
rsync -a "$WORK/runtime/runtime-home/" "$WORK/rootfs/opt/jottabox-live/runtime-home/"
cp "$WORK/runtime/source-home.txt" "$WORK/rootfs/opt/jottabox-live/source-home.txt"
cp "$WORK/runtime/jottabox-version.txt" "$WORK/rootfs/opt/jottabox-live/jottabox-version.txt"

chmod +x   "$WORK/rootfs/usr/local/bin/jottabox-session"   "$WORK/rootfs/usr/local/bin/jottabox-prepare-home"   "$WORK/rootfs/usr/local/bin/jottabox-install-system"

# Copia os Flatpaks do golden master para a imagem, se existirem.
# Isso torna a primeira ISO realmente utilizável offline para os emuladores já instalados.
if [[ -d /var/lib/flatpak ]]; then
  echo ">>> Incorporando Flatpaks do golden master"
  mkdir -p "$WORK/rootfs/var/lib/flatpak"
  rsync -aHAX --delete /var/lib/flatpak/ "$WORK/rootfs/var/lib/flatpak/"
fi

# Cria atalho gráfico dentro do runtime para instalação posterior.
mkdir -p "$WORK/rootfs/usr/share/applications"
cat > "$WORK/rootfs/usr/share/applications/jottabox-install.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Instalar JottaBox
Comment=Instalar o JottaBox neste computador
Exec=/usr/local/bin/jottabox-install-system
Icon=system-software-install
Terminal=false
Categories=System;
EOF

echo ">>> Recriando SquashFS"
mksquashfs "$WORK/rootfs" "$WORK/filesystem-new.squashfs" -comp xz -noappend >/dev/null

echo ">>> Gerando ISO híbrida"
rm -f "$OUTPUT"
xorriso   -indev "$BASE_ISO"   -outdev "$OUTPUT"   -boot_image any replay   -map "$WORK/filesystem-new.squashfs" /casper/filesystem.squashfs   -commit >/dev/null 2>&1

echo
echo "=============================================="
echo " JottaBox Live $LIVE_VERSION criada"
echo "=============================================="
echo "ISO: $OUTPUT"
du -h "$OUTPUT"
sha256sum "$OUTPUT" | tee "$OUTPUT.sha256"
echo
echo "Grave a ISO em um pendrive e faça o primeiro teste em modo Live."
