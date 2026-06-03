#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ==========================================================================
# 0. Configuration Defaults & Argument Parsing
# ==========================================================================
INSTALL_SYS_DEPS=true
INSTALL_XIMEA=false
INSTALL_ARAVIS=false
INSTALL_THORLABS=false
AUTO_YES=false
INSTALL_ALL=false

show_help() {
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-sys-deps   Skip apt-get system dependency installation"
    echo "  --with-ximea      Install XIMEA camera drivers & bindings"
    echo "  --with-aravis     Compile and install Aravis (GigE/USB3 cameras)"
    echo "  --with-thorlabs   Fetch Thorlabs Spectrophotometer firmware"
    echo "  --all             Install all optional hardware components (XIMEA, Aravis, Thorlabs)"
    echo "  -y, --yes         Skip all interactive prompts (assume yes)"
    echo "  -h, --help        Show this help menu"
    exit 0
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-sys-deps) INSTALL_SYS_DEPS=false ;;
        --with-ximea)     INSTALL_XIMEA=true ;;
        --with-aravis)    INSTALL_ARAVIS=true ;;
        --with-thorlabs)  INSTALL_THORLABS=true ;;
        --all)            INSTALL_ALL=true ;; 
        -y|--yes)         AUTO_YES=true ;;
        -h|--help)        show_help ;;
        *) echo "[-] Unknown parameter: $1"; show_help; exit 1 ;;
    esac
    shift
done

if [ "$INSTALL_ALL" = "true" ]; then
    INSTALL_XIMEA=true
    INSTALL_ARAVIS=true
    INSTALL_THORLABS=true
fi

echo "========================================="
echo "       ZebVR Installation Script        "
echo "========================================="

# 1. Guardrail: Prevent running the whole script with sudo/root
if [ "$EUID" -eq 0 ]; then
  echo "[-] Error: Please do NOT run this script as root or with sudo directly."
  echo "    Run it as a normal user: ./install.sh"
  echo "    The script will prompt you for your sudo password when necessary."
  exit 1
fi

# Capture the native environment values safely
REAL_USER="$USER"
USER_HOME="$HOME"
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 2. Install Core System Dependencies via apt
if [ "$INSTALL_SYS_DEPS" = "true" ]; then
    echo "[+] Installing system dependencies (may prompt for sudo password)..."
    sudo apt-get update
    sudo apt-get install -y libportaudio2 build-essential libusb-1.0-0-dev innoextract curl python3-yaml
else
    echo "[+] Skipping core system dependencies (--skip-sys-deps passed)."
fi

# 3. Labjack Exodriver Setup
echo "[+] Checking Labjack Exodriver..."
if [ -f "/usr/local/lib/liblabjackusb.so" ] || [ -f "/usr/lib/liblabjackusb.so" ]; then
    echo "[+] Labjack Exodriver is already installed. Skipping compilation."
else
    echo "[+] Labjack Exodriver not found. Installing from source..."
    if [ ! -d "exodriver" ]; then
        git clone https://github.com/labjack/exodriver.git
    fi
    cd exodriver
    # Run their installer with sudo as it writes to /usr/local/lib
    sudo ./install.sh
    cd ..
    rm -rf exodriver
    echo "[+] Labjack Exodriver successfully installed."
fi

# 4. Hardware Permissions & Udev Rules
echo "[+] Adding '$REAL_USER' to plugdev and dialout groups..."
sudo usermod -a -G plugdev,dialout "$REAL_USER"

echo "[+] Writing Thorlabs udev rules..."
# Using sudo tee allows writing safely to a protected system directory
sudo tee /etc/udev/rules.d/99-thorlabs.rules > /dev/null << 'EOF'
SUBSYSTEMS=="usb", ATTRS{idVendor}=="1313", GROUP="plugdev", MODE="0666"
EOF

echo "[+] Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# 5. Locate or Install Mamba/Conda
echo "[+] Locating mamba / conda installation..."
MAMBA_EXE=""

USER_WHICH=$(command -v mamba 2>/dev/null || command -v conda 2>/dev/null || true)
if [ -n "$USER_WHICH" ] && [ -f "$USER_WHICH" ]; then
    MAMBA_EXE="$USER_WHICH"
fi

# If conda/mamba is completely missing, offer to install it automatically
if [ -z "$MAMBA_EXE" ] || [ ! -f "$MAMBA_EXE" ]; then
    echo "[-] conda/mamba was not found on this system."
    
    install_miniforge="n"
    if [ "$AUTO_YES" = "true" ]; then
        install_miniforge="y"
    else
        # Redirecting to /dev/tty guarantees interactive prompting works smoothly
        exec </dev/tty
        read -p "[?] Would you like to automatically download and install Miniforge3 for $REAL_USER? (y/n): " install_miniforge
    fi
    
    if [ "$install_miniforge" = "y" ] || [ "$install_miniforge" = "Y" ]; then
        echo "[+] Downloading Miniforge installer..."
        MINIFORGE_SH="/tmp/Miniforge3-Linux-x86_64.sh"
        
        curl -L https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -o "$MINIFORGE_SH"
        
        echo "[+] Installing Miniforge to $USER_HOME/miniforge3..."
        bash "$MINIFORGE_SH" -b -p "$USER_HOME/miniforge3"
        rm -f "$MINIFORGE_SH"
        
        "$USER_HOME/miniforge3/bin/conda" init bash
        
        MAMBA_EXE="$USER_HOME/miniforge3/bin/mamba"
        echo "[+] Miniforge successfully installed!"
        echo "[!] NOTE: You may need to run 'source ~/.bashrc' after this script completes."
    else
        echo "[-] Error: Miniforge/Conda is required to manage ZebVR environments. Aborting installation."
        exit 1
    fi
fi

echo "[+] Using conda/mamba binary: $MAMBA_EXE"

# 6. Parse dynamic Environment Name from ZebVR.yml & Create/Update Environment
if [ ! -f "ZebVR.yml" ]; then
    echo "[-] Error: ZebVR.yml file not found in current directory."
    exit 1
fi

# Use Python to safely parse the exact name string out of the YAML file
ENV_NAME=$(python3 -c "import yaml; print(yaml.safe_load(open('ZebVR.yml'))['name'])" 2>/dev/null || true)

# Fallback basic parser if python3-yaml fails for any reason
if [ -z "$ENV_NAME" ]; then
    ENV_NAME=$(grep '^name:' ZebVR.yml | awk '{print $2}' | tr -d '\r\n[:space:]')
fi

if [ -z "$ENV_NAME" ]; then
    echo "[-] Error: Could not extract environment name from ZebVR.yml."
    exit 1
fi

echo "[+] Parsed target environment name: '$ENV_NAME'"

if "$MAMBA_EXE" env list --json | grep -q "/$ENV_NAME\""; then
    update_env="n"
    if [ "$AUTO_YES" = "true" ]; then
        update_env="y"
    else
        exec </dev/tty
        read -p "[?] Conda environment '$ENV_NAME' already exists. Would you like to update/repair it using ZebVR.yml? (y/n): " update_env
    fi

    if [ "$update_env" = "y" ] || [ "$update_env" = "Y" ]; then
        echo "[+] Updating environment '$ENV_NAME'..."
        "$MAMBA_EXE" env update -f ZebVR.yml --prune
    else
        echo "[-] Skipping environment update. Proceeding with existing '$ENV_NAME' environment."
    fi
else
    echo "[+] Creating Conda environment '$ENV_NAME' from ZebVR.yml..."
    "$MAMBA_EXE" env create -f ZebVR.yml --yes
fi

# --- XIMEA Setup ---
if [ "$INSTALL_XIMEA" = "false" ] && [ "$AUTO_YES" = "false" ]; then
    exec </dev/tty
    read -p "[?] Do you want to install XIMEA Camera drivers & bindings? (y/n): " prompt_ximea
    if [[ "$prompt_ximea" =~ ^[Yy]$ ]]; then INSTALL_XIMEA=true; fi
fi

if [ "$INSTALL_XIMEA" = "true" ]; then
    echo "[+] Running XIMEA setup scripts..."

    XIMEA_FLAGS=""
    if [ "$AUTO_YES" = "true" ]; then
        XIMEA_FLAGS="-y"
    fi

    "$MAMBA_EXE" run -n "$ENV_NAME" python scripts/setup_ximea.py $XIMEA_FLAGS
    
    if [ -f "install_ximea_systemd_service.sh" ]; then
        echo "[+] Configuring automated XIMEA systemd maintenance service..."
        chmod +x install_ximea_systemd_service.sh
        sudo ./install_ximea_systemd_service.sh
    else
        echo "[-] Warning: install_ximea_systemd_service.sh not found. Skipping service setup."
    fi
fi

# --- Aravis Setup ---
if [ "$INSTALL_ARAVIS" = "false" ] && [ "$AUTO_YES" = "false" ]; then
    exec </dev/tty
    read -p "[?] Do you want to compile and install Aravis (GigE/USB3 cameras)? (y/n): " prompt_aravis
    if [[ "$prompt_aravis" =~ ^[Yy]$ ]]; then INSTALL_ARAVIS=true; fi
fi

if [ "$INSTALL_ARAVIS" = "true" ]; then
    echo "[+] Building Aravis from source..."
    CONDA_PREFIX_DIR=$("$MAMBA_EXE" run -n "$ENV_NAME" python -c "import os; print(os.environ['CONDA_PREFIX'])")
    
    git clone https://github.com/AravisProject/aravis.git
    cd aravis

    "$MAMBA_EXE" run -n "$ENV_NAME" meson setup build --prefix="$CONDA_PREFIX_DIR" -Dintrospection=enabled -Dviewer=disabled -Dtests=true --libdir=lib
    "$MAMBA_EXE" run -n "$ENV_NAME" ninja -C build install
    cd ..
    rm -rf aravis
    echo "[+] Aravis successfully compiled into active Conda environment."
fi

# --- Thorlabs Firmware ---
if [ "$INSTALL_THORLABS" = "false" ] && [ "$AUTO_YES" = "false" ]; then
    exec </dev/tty
    read -p "[?] Do you want to fetch Thorlabs Spectrophotometer firmware? (y/n): " prompt_thor
    if [[ "$prompt_thor" =~ ^[Yy]$ ]]; then INSTALL_THORLABS=true; fi
fi

if [ "$INSTALL_THORLABS" = "true" ]; then
    echo "[+] Downloading Thorlabs firmware..."
    "$MAMBA_EXE" run -n "$ENV_NAME" python -m thorlabs_ccs.get_firmware
fi

# --- Desktop Entry Entry ---
echo "[+] Creating Linux Desktop Application Entry..."
DESKTOP_ENTRY_DIR="$USER_HOME/.local/share/applications"
mkdir -p "$DESKTOP_ENTRY_DIR"

cat <<EOF > "$DESKTOP_ENTRY_DIR/zebvr.desktop"
[Desktop Entry]
Version=0.1
Type=Application
Name=ZebVR
Comment=Launch the ZebVR Virtual Reality System
Exec=$MAMBA_EXE run -n $ENV_NAME python -m ZebVR
Path=$REPO_DIR
Icon=$REPO_DIR/ZebVR/resources/zebvr.png
Terminal=true
Categories=Science;Education;Development;
EOF

chmod +x "$DESKTOP_ENTRY_DIR/zebvr.desktop"
echo "[+] Desktop entry created! ZebVR will now show up in your system applications menu."

# ==========================================================================
# Final Status Display
# ==========================================================================
MAMBA_BIN_NAME=$(basename "$MAMBA_EXE")

echo "=========================================================================="
echo "[+] SYSTEM INSTALLATION COMPLETE!"
echo "=========================================================================="
echo " IMPORTANT NEXT STEPS:"
echo " 1. You MUST log out and log back in (or reboot) for hardware group"
echo "    permissions (plugdev/dialout) to take effect."
echo " 2. If you installed XIMEA drivers, Secure Boot might need to be"
echo "    disabled in your system BIOS if the kernel module fails to load."
echo " 3. To activate this specific branch environment, run:"
echo "    $MAMBA_BIN_NAME activate $ENV_NAME"
echo "=========================================================================="