#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================="
echo "       ZebVR Uninstallation Script       "
echo "========================================="

# 1. Guardrail: Prevent running the whole script with sudo/root
if [ "$EUID" -eq 0 ]; then
  echo "[-] Error: Please do NOT run this script as root or with sudo directly."
  echo "    Run it as a normal user: ./uninstall.sh"
  echo "    The script will prompt you for your sudo password when necessary."
  exit 1
fi

REAL_USER="$USER"
USER_HOME="$HOME"

# Ensure we can prompt the user interactively
exec </dev/tty

# --------------------------------------------------------------------------
# 2. Locate Miniforge (Mamba/Conda) and Parse Environment Name
# --------------------------------------------------------------------------
echo "[+] Locating Miniforge installation..."
MAMBA_EXE=""

USER_WHICH=$(command -v mamba 2>/dev/null || true)
if [ -n "$USER_WHICH" ] && [ -f "$USER_WHICH" ]; then
    MAMBA_EXE="$USER_WHICH"
fi
if [ -z "$MAMBA_EXE" ] && [ -f "$USER_HOME/miniforge3/bin/mamba" ]; then
    MAMBA_EXE="$USER_HOME/miniforge3/bin/mamba"
fi
if [ -z "$MAMBA_EXE" ] && [ -f "$USER_HOME/miniforge3/bin/conda" ]; then
    MAMBA_EXE="$USER_HOME/miniforge3/bin/conda"
fi

ENV_NAME=""
if [ -f "ZebVR.yml" ]; then
    ENV_NAME=$(python3 -c "import yaml; print(yaml.safe_load(open('ZebVR.yml'))['name'])" 2>/dev/null || true)
    if [ -z "$ENV_NAME" ]; then
        ENV_NAME=$(grep '^name:' ZebVR.yml | awk '{print $2}' | tr -d '\r\n[:space:]')
    fi
fi

# If ZebVR.yml is missing, ask the user manually so we can still clean up
if [ -z "$ENV_NAME" ]; then
    read -p "[?] Could not auto-detect environment name. Enter Conda environment name to remove (Default: zebvr): " ENV_NAME
    ENV_NAME=${ENV_NAME:-zebvr}
fi

# --------------------------------------------------------------------------
# 3. Remove Conda/Mamba Environment
# --------------------------------------------------------------------------
if [ -n "$MAMBA_EXE" ] && [ -f "$MAMBA_EXE" ]; then
    if "$MAMBA_EXE" env list --json | grep -q "/$ENV_NAME\""; then
        read -p "[?] Do you want to delete the Conda environment '$ENV_NAME'? (y/n): " remove_env
        if [ "$remove_env" = "y" ] || [ "$remove_env" = "Y" ]; then
            echo "[+] Removing Conda environment '$ENV_NAME'..."
            "$MAMBA_EXE" env remove -n "$ENV_NAME" --yes
            echo "[+] Environment removed."
        fi
    else
        echo "[-] Conda environment '$ENV_NAME' not found. Skipping."
    fi
else
    echo "[-] Miniforge/Mamba binary not found. Skipping environment removal."
fi

# --------------------------------------------------------------------------
# 4. Remove XIMEA Systemd Service (Optional Component)
# --------------------------------------------------------------------------
echo "-----------------------------------------"
echo "Cleaning Optional Hardware Configurations"
echo "-----------------------------------------"

# Check for a standard XIMEA service file location or pattern
XIMEA_SERVICE="/etc/systemd/system/ximea-startup.service"
XIMEA_SCRIPT="/usr/local/bin/ximea_fix_driver.sh"

# Check if either the service or the script exists
if [ -f "$XIMEA_SERVICE" ] || [ -f "$XIMEA_SCRIPT" ]; then
    read -p "[?] XIMEA systemd service or maintenance script detected. Remove them? (y/n): " remove_ximea
    if [ "$remove_ximea" = "y" ] || [ "$remove_ximea" = "Y" ]; then
        
        if [ -f "$XIMEA_SERVICE" ]; then
            SERVICE_NAME=$(basename "$XIMEA_SERVICE")
            echo "[+] Disabling and removing $SERVICE_NAME..."
            sudo systemctl stop "$SERVICE_NAME" || true
            sudo systemctl disable "$SERVICE_NAME" || true
            sudo rm -f "$XIMEA_SERVICE"
            sudo systemctl daemon-reload
        fi

        if [ -f "$XIMEA_SCRIPT" ]; then
            echo "[+] Removing background utility script: $XIMEA_SCRIPT"
            sudo rm -f "$XIMEA_SCRIPT"
        fi
        
        echo "[+] XIMEA components successfully purged."
    fi
fi

# --------------------------------------------------------------------------
# 5. Remove Thorlabs Udev Rules
# --------------------------------------------------------------------------
THORLABS_RULES="/etc/udev/rules.d/99-thorlabs.rules"
if [ -f "$THORLABS_RULES" ]; then
    read -p "[?] Do you want to remove Thorlabs udev rules? (y/n): " remove_udev
    if [ "$remove_udev" = "y" ] || [ "$remove_udev" = "Y" ]; then
        echo "[+] Removing $THORLABS_RULES..."
        sudo rm -f "$THORLABS_RULES"
        echo "[+] Reloading udev rules..."
        sudo udevadm control --reload-rules
        sudo udevadm trigger
    fi
fi

# --------------------------------------------------------------------------
# 6. Uninstall Labjack Exodriver
# --------------------------------------------------------------------------
LABJACK_LIB1="/usr/local/lib/liblabjackusb.so"
LABJACK_LIB2="/usr/lib/liblabjackusb.so"

if [ -f "$LABJACK_LIB1" ] || [ -f "$LABJACK_LIB2" ]; then
    read -p "[?] Labjack Exodriver detected. Do you want to remove it? (y/n): " remove_labjack
    if [ "$remove_labjack" = "y" ] || [ "$remove_labjack" = "Y" ]; then
        echo "[+] Removing Labjack Exodriver binaries and rules..."
        sudo rm -f "/usr/local/lib/liblabjackusb.*"
        sudo rm -f "/usr/lib/liblabjackusb.*"
        sudo rm -f "/lib/udev/rules.d/10-labjack.rules" || true
        sudo rm -f "/etc/udev/rules.d/10-labjack.rules" || true
        echo "[+] Labjack Exodriver removed."
    fi
fi

# --------------------------------------------------------------------------
# 7. User Group Cleanup (Optional)
# --------------------------------------------------------------------------
read -p "[?] Do you want to remove '$REAL_USER' from plugdev and dialout groups? (y/n): " remove_groups
if [ "$remove_groups" = "y" ] || [ "$remove_groups" = "Y" ]; then
    echo "[+] Removing '$REAL_USER' from groups..."
    # Note: gpasswd -d safely removes a user from a group
    sudo gpasswd -d "$REAL_USER" plugdev || true
    sudo gpasswd -d "$REAL_USER" dialout || true
fi

echo "=========================================================================="
echo "[+] UNINSTALLATION PROCESS COMPLETE!"
echo "=========================================================================="
echo " NOTE:"
echo " 1. Base system applications installed via apt (like curl, python3-yaml,"
echo "    build-essential) and Miniforge itself were kept to prevent disrupting"
echo "    other environments on your machine."
echo " 2. Log out and log back in for group changes to finalize."
echo "=========================================================================="