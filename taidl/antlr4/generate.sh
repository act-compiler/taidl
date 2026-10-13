#!/bin/bash
# Regenerate the IDLV2 lexer, parser, listener and visitor from IDLV2.g4.
set -euo pipefail

cd "$(dirname "$0")"

# The tool must match the antlr4-python3-runtime pin.
ANTLR_JAR="${ANTLR_JAR:-/opt/antlr/antlr-4.9.2-complete.jar}"

java -jar "$ANTLR_JAR" -Dlanguage=Python3 -visitor IDLV2.g4
