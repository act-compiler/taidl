#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
source act.env

ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    IMAGE_NAME="devanshdvj/act:${ACT_DOCKERHUB_TAG}-amd64"
elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    IMAGE_NAME="devanshdvj/act:${ACT_DOCKERHUB_TAG}-arm64"
else
    echo "Error: Unsupported architecture: $ARCH"
    exit 1
fi

HOST_MOUNT="$(pwd)/.."

docker run --rm --entrypoint bash \
  -v "${HOST_MOUNT}:/workspace:rw" \
  -w /workspace \
  "${IMAGE_NAME}" \
  -ilc "$*"
