#!/usr/bin/env bash
set -Eeuo pipefail

RPCS3_APP="net.rpcs3.RPCS3"

DISPLAY_VALUE="${DISPLAY:-:0}"
XAUTH_VALUE="${XAUTHORITY:-$HOME/.Xauthority}"

RPCS3_CFG="$HOME/.var/app/$RPCS3_APP/config/rpcs3"
DEV_FLASH="$RPCS3_CFG/dev_flash"

STATE="$HOME/.local/share/jottabox"
FIRMWARE_DIR="$STATE/firmware"
PUP="$FIRMWARE_DIR/PS3UPDAT.PUP"

mkdir -p "$FIRMWARE_DIR"

has_firmware() {
    find "$DEV_FLASH/data/font" \
        -maxdepth 1 \
        -type f \
        2>/dev/null |
        grep -q .
}

if has_firmware; then
    echo "Firmware do PS3 já instalado."
    exit 0
fi

echo "Firmware do PS3 não encontrado."

if [[ ! -f "$PUP" ]]; then
    echo ">>> Baixando firmware oficial do PlayStation 3"

    # Firmware oficial Sony / PlayStation 3 4.93.
    HOST="dbr01.ps3.update.playstation.net"
    PATH_FW="/update/ps3/image/br/2026_0318_a2b60b6ac1d2e49e230144345616927c/PS3UPDAT.PUP"
    URL="https://${HOST}${PATH_FW}"

    TMP="${PUP}.part"

    rm -f "$TMP"

    curl \
        -fL \
        --retry 3 \
        --connect-timeout 30 \
        "$URL" \
        -o "$TMP"

    SIZE="$(stat -c %s "$TMP")"

    if (( SIZE < 100000000 )); then
        echo "ERRO: firmware baixado parece inválido."
        echo "Tamanho recebido: $SIZE bytes"
        rm -f "$TMP"
        exit 10
    fi

    mv -f "$TMP" "$PUP"

    echo "Firmware baixado:"
    echo "$PUP"
fi

echo
echo ">>> Abrindo instalador de firmware do RPCS3"
echo "Confirme a instalação na tela do JottaBox."

export DISPLAY="$DISPLAY_VALUE"
export XAUTHORITY="$XAUTH_VALUE"

flatpak run \
    --user \
    "$RPCS3_APP" \
    --installfw "$PUP"

echo
echo ">>> Verificando firmware"

if has_firmware; then
    echo "Firmware instalado com sucesso."
    exit 0
fi

echo "ERRO: firmware ainda não foi detectado pelo RPCS3."
exit 11
