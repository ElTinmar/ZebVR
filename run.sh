#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Get the absolute directory of THIS script
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change directory to the repository root to prevent FileNotFoundErrors
cd "$REPO_DIR"

echo "========================================="
echo "          Launching ZebVR...             "
echo "========================================="

# 1. Locate Miniforge/Mamba dynamically
USER_HOME="$HOME"
MAMBA_EXE=$(command -v mamba 2>/dev/null || command -v conda 2>/dev/null || true)

if [ -z "$MAMBA_EXE" ]; then
    echo "[-] Error: Miniforge/Mamba installation not found."
    echo "    Please run ./install.sh first."
    exit 1
fi

# 2. Extract environment name dynamically from ZebVR.yml
if [ -f "ZebVR.yml" ]; then
    ENV_NAME=$(python3 -c "import yaml; print(yaml.safe_load(open('ZebVR.yml'))['name'])" 2>/dev/null || true)
    if [ -z "$ENV_NAME" ]; then
        ENV_NAME=$(grep '^name:' ZebVR.yml | awk '{print $2}' | tr -d '\r\n[:space:]')
    fi
fi
ENV_NAME=${ENV_NAME:-ZebVR_dev} # Fallback to ZebVR_dev if parsing fails

# 3. Execute the module inside the correct environment
echo "[+] Using environment: $ENV_NAME"
exec "$MAMBA_EXE" run -n "$ENV_NAME" python -m ZebVR