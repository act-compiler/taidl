#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
source act.env

ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
  IMAGE_NAME="devanshdvj/act-env:${ACT_ENV_TAG}-amd64"
elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
  IMAGE_NAME="devanshdvj/act-env:${ACT_ENV_TAG}-arm64"
else
  echo "Error: Unsupported architecture: $ARCH"
  exit 1
fi

HOST_MOUNT="$(pwd)/.."
# One name per run, for the trap
CONTAINER_NAME="taidl-exec-$$-${RANDOM}"

# Remove the container and restore the caller's ownership
restore_ownership() {
  local status=$?
  # Already gone after a run that ends itself
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  ./chown.sh >/dev/null 2>&1 || echo "warning: could not restore the ownership of the files this run wrote" >&2
  exit "$status"
}
trap restore_ownership EXIT
# A signal ends the run at once, with its status
trap 'exit 130' INT
trap 'exit 143' TERM

# In the foreground, so a signal waits for it
docker create --rm --name "${CONTAINER_NAME}" --entrypoint bash \
  -v "${HOST_MOUNT}:/workspace:rw" \
  -w /workspace \
  "${IMAGE_NAME}" \
  -ilc "$*" >/dev/null
# In the background, so a signal reaches the trap
docker start -a "${CONTAINER_NAME}" &
wait $!
