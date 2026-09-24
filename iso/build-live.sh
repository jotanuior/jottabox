#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

BASE_ISO="${1:-}"
RUNTIME="${2:-}"
LIVE_VERSION="$(cat "$ROOT/LIVE_VERSION" 2>/dev/null || echo 0.1.2)"
OUTPUT="${3:-$PWD/JottaBox-Live-${LIVE_VERSION}.iso}"

[[ -f "$BASE_ISO" ]] || {
    echo "Uso: sudo $0 linuxmint.iso jottabox-live-runtime.tar.gz [saida.iso]"
    exit 2
}

[[ -f "$RUNTIME" ]] || {
    echo "Runtime não encontrado: $RUNTIME"
    exit 2
}

[[ "$EUID" -eq 0 ]] || {
    echo "Execute com sudo."
    exit 2
}

for c in xorriso unsquashfs mksquashfs rsync tar chroot apt-get; do
    command -v "$c" >/dev/null 2>&1 || {
        echo "Falta: $c"
        echo "Instale: apt install xorriso squashfs-tools rsync"
        exit 1
    }
done

WORK="$(mktemp -d /tmp/jottabox-live.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/rootfs" "$WORK/runtime"

echo ">>> Extraindo filesystem.squashfs"

xorriso \
    -osirrox on \
    -indev "$BASE_ISO" \
    -extract /casper/filesystem.squashfs "$WORK/filesystem.squashfs" \
    >/dev/null 2>&1

echo ">>> Abrindo SquashFS"

unsquashfs \
    -d "$WORK/rootfs" \
    "$WORK/filesystem.squashfs" \
    >/dev/null

echo ">>> Aplicando overlay JottaBox Live"

rsync -a \
    "$ROOT/rootfs-overlay/" \
    "$WORK/rootfs/"

echo ">>> Preparando Microsoft Edge"

EDGE_VERSION="$(
    dpkg-query -W -f='${Version}' microsoft-edge-stable 2>/dev/null || true
)"

(
    cd "$WORK"

    if [[ -n "$EDGE_VERSION" ]]; then
        apt-get download "microsoft-edge-stable=$EDGE_VERSION"
    else
        apt-get download microsoft-edge-stable
    fi
)

EDGE_DEB="$(
    find "$WORK" \
        -maxdepth 1 \
        -type f \
        -name 'microsoft-edge-stable_*.deb' \
        | head -n1
)"

[[ -f "$EDGE_DEB" ]] || {
    echo "ERRO: não foi possível baixar o Microsoft Edge."
    exit 1
}

cp \
    "$EDGE_DEB" \
    "$WORK/rootfs/tmp/microsoft-edge-stable.deb"

echo ">>> Instalando dependências do JottaBox no Live"

cp -L \
    /etc/resolv.conf \
    "$WORK/rootfs/etc/resolv.conf"

chroot "$WORK/rootfs" /bin/bash -c '
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

UPDATE_OK=0

for ATTEMPT in 1 2 3 4 5; do
    echo ">>> apt update tentativa $ATTEMPT/5"

    rm -rf /var/lib/apt/lists/*
    mkdir -p /var/lib/apt/lists/partial

    if apt-get \
        -o Acquire::Retries=3 \
        -o Acquire::http::No-Cache=true \
        update
    then
        UPDATE_OK=1
        break
    fi

    echo ">>> Espelho em sincronização. Aguardando 30 segundos..."
    sleep 30
done

if [[ "$UPDATE_OK" != "1" ]]; then
    echo "ERRO: não foi possível atualizar os índices APT após 5 tentativas."
    exit 1
fi

apt-get install -y --no-install-recommends \
    python3-pygame \
    rsync \
    flatpak \
    ca-certificates \
    curl \
    udisks2 \
    zenity \
    steam-devices

apt-get install -y /tmp/microsoft-edge-stable.deb

rm -f /tmp/microsoft-edge-stable.deb

apt-get clean
rm -rf /var/lib/apt/lists/*
'

echo ">>> Baixando Better xCloud"

BETTER_XCLOUD_URL="https://github.com/redphx/better-xcloud/releases/latest/download/better-xcloud.user.js"

mkdir -p "$WORK/rootfs/opt/jottabox-live"

curl -fL \
    --retry 3 \
    --retry-delay 3 \
    "$BETTER_XCLOUD_URL" \
    -o "$WORK/rootfs/opt/jottabox-live/better-xcloud.user.js"

[[ -s "$WORK/rootfs/opt/jottabox-live/better-xcloud.user.js" ]] || {
    echo "ERRO: Better xCloud não foi baixado."
    exit 1
}

echo ">>> Incorporando runtime JottaBox"

tar \
    -C "$WORK/runtime" \
    -xzf "$RUNTIME"

mkdir -p \
    "$WORK/rootfs/opt/jottabox-live"

rsync -a \
    "$WORK/runtime/runtime-home/" \
    "$WORK/rootfs/opt/jottabox-live/runtime-home/"

cp \
    "$WORK/runtime/source-home.txt" \
    "$WORK/rootfs/opt/jottabox-live/source-home.txt"

cp \
    "$WORK/runtime/jottabox-version.txt" \
    "$WORK/rootfs/opt/jottabox-live/jottabox-version.txt"

chmod +x \
    "$WORK/rootfs/usr/local/bin/jottabox-session" \
    "$WORK/rootfs/usr/local/bin/jottabox-prepare-home" \
    "$WORK/rootfs/usr/local/bin/jottabox-install-system" \
    "$WORK/rootfs/usr/local/bin/jottabox-autostart" \
    "$WORK/rootfs/usr/local/bin/jottabox-external-roms" \
    "$WORK/rootfs/usr/local/bin/jottabox-rom-storage" \
    2>/dev/null || true

echo ">>> Incorporando Flatpaks do golden master"

[[ -d /var/lib/flatpak ]] || {
    echo "ERRO: /var/lib/flatpak não existe no golden master."
    exit 1
}

mkdir -p \
    "$WORK/rootfs/var/lib/flatpak"

rsync -aHAX --delete \
    /var/lib/flatpak/ \
    "$WORK/rootfs/var/lib/flatpak/"

echo ">>> Validando Flatpaks copiados"

for APP in \
    com.valvesoftware.Steam \
    org.libretro.RetroArch \
    org.ppsspp.PPSSPP \
    org.DolphinEmu.dolphin-emu \
    net.pcsx2.PCSX2
do
    if [[ ! -d "$WORK/rootfs/var/lib/flatpak/app/$APP" ]]; then
        echo "ERRO: Flatpak ausente no Live: $APP"
        exit 1
    fi

    echo "OK: $APP"
done

echo ">>> Validando Microsoft Edge"

chroot "$WORK/rootfs" \
    test -x /usr/bin/microsoft-edge-stable \
    || {
        echo "ERRO: Microsoft Edge não foi instalado no Live."
        exit 1
    }

echo ">>> Criando atalho de instalação"

mkdir -p \
    "$WORK/rootfs/usr/share/applications"

cat > "$WORK/rootfs/usr/share/applications/jottabox-install.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Instalar JottaBox
Comment=Instalar o JottaBox neste computador
Exec=/usr/local/bin/jottabox-install-system
Icon=system-software-install
Terminal=false
Categories=System;
DESKTOP

echo ">>> Recriando SquashFS"

mksquashfs \
    "$WORK/rootfs" \
    "$WORK/filesystem-new.squashfs" \
    -comp xz \
    -noappend \
    >/dev/null

echo ">>> Gerando ISO híbrida"

rm -f "$OUTPUT"

xorriso \
    -indev "$BASE_ISO" \
    -outdev "$OUTPUT" \
    -boot_image any replay \
    -map "$WORK/filesystem-new.squashfs" /casper/filesystem.squashfs \
    -commit \
    >/dev/null 2>&1

echo
echo "=============================================="
echo " JottaBox Live $LIVE_VERSION criada"
echo "=============================================="
echo "ISO: $OUTPUT"

du -h "$OUTPUT"

sha256sum "$OUTPUT" | tee "$OUTPUT.sha256"

echo
echo "Grave a ISO em um pendrive e faça o primeiro teste em modo Live."
