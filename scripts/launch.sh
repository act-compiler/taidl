#!/bin/bash

set -e

docker stop taidl-main >/dev/null 2>&1 || true
docker stop taidl-baseline >/dev/null 2>&1 || true

cd "$(dirname "$0")/../"
HOST_MOUNT="$(pwd)"

UID_N="$(id -u)"
GID_N="$(id -g)"

# Detect architecture
ARCH=$(uname -m)

if [[ "$ARCH" == "x86_64" ]]; then
    TAIDL_IMAGE_NAME="devanshdvj/taidl-micro25-artifact:amd64"
    GPU_FLAG=$(command -v nvidia-smi >/dev/null 2>&1 && echo "--gpus all" || echo "")

    if [ -n "$GPU_FLAG" ]; then
        if (! docker info 2>/dev/null | grep -q 'nvidia' || ! command -v nvidia-container-runtime >/dev/null 2>&1); then
            echo "Warning: NVIDIA GPU detected but the NVIDIA Container Toolkit is not set up properly."
            echo "Running without GPU support."
            GPU_FLAG=""
        else
            echo "NVIDIA GPU detected. Running with GPU support."
        fi
    else
        echo "No GPU detected. Running without GPU support."
    fi
elif [[ "$ARCH" == "arm64" ]] || [[ "$ARCH" == "aarch64" ]]; then
    TAIDL_IMAGE_NAME="devanshdvj/taidl-micro25-artifact:arm64"
    GPU_FLAG=""
else
    echo "Error: Unsupported architecture: $ARCH"
    exit 1
fi

$HOST_MOUNT/scripts/setup.sh

echo "Starting interactive TAIDL container for $ARCH"
if [ -n "$GPU_FLAG" ]; then
    echo "Using GPU support: $GPU_FLAG"
fi

docker run --rm -it $GPU_FLAG \
    -v "$HOST_MOUNT:/taidl" \
    -w /taidl \
    $TAIDL_IMAGE_NAME \
    bash

# Fix ownership
docker run --rm --name taidl-main \
    -v "$HOST_MOUNT:/taidl" \
    $TAIDL_IMAGE_NAME \
    bash -c "chown -R ${UID_N}:${GID_N} /taidl/*"
