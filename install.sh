#!/usr/bin/env bash
# TruthGPT Universal Installer Entry Point
SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
exec "$SCRIPT_DIR/install_truth.sh" "$@"
