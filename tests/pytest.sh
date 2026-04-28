#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

./docker/exec.sh \
  "pip install -e . -q && \
  pip install pytest -q && \
  pytest tests/"
