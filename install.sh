#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

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
echo "[+] Installing system dependencies (may prompt for sudo password)..."
sudo apt-get update
sudo apt-get install -y libportaudio2 build-essential libusb-1.0-0-dev innoextract curl python3-yaml

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


# 5. Locate or Install Miniforge (Mamba/Conda)
echo "[+] Locating Miniforge installation..."
MAMBA_EXE=""

# Method A: Use 'command -v' to see if mamba is already in the user's path
USER_WHICH=$(command -v mamba 2>/dev/null || true)
if [ -n "$USER_WHICH" ] && [ -f "$USER_WHICH" ]; then
    MAMBA_EXE="$USER_WHICH"
fi

# Method B: Check standard absolute default user directories for Miniforge
if [ -z "$MAMBA_EXE" ]; then
    if [ -f "$USER_HOME/miniforge3/bin/mamba" ]; then
        MAMBA_EXE="$USER_HOME/miniforge3/bin/mamba"
    fi
fi

# Method C: Fallback to conda inside miniforge if mamba wrapper isn't explicitly targeted
if [ -z "$MAMBA_EXE" ] && [ -f "$USER_HOME/miniforge3/bin/conda" ]; then
    MAMBA_EXE="$USER_HOME/miniforge3/bin/conda"
fi

# Method D: If Miniforge is completely missing, offer to install it automatically
if [ -z "$MAMBA_EXE" ] || [ ! -f "$MAMBA_EXE" ]; then
    echo "[-] Miniforge was not found on this system."
    # Redirecting to /dev/tty guarantees interactive prompting works smoothly
    exec </dev/tty
    read -p "[?] Would you like to automatically download and install Miniforge3 for $REAL_USER? (y/n): " install_miniforge
    
    if [ "$install_miniforge" = "y" ] || [ "$install_miniforge" = "Y" ]; then
        echo "[+] Downloading Miniforge installer..."
        MINIFORGE_SH="/tmp/Miniforge3-Linux-x86_64.sh"
        
        curl -L https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -o "$MINIFORGE_SH"
        
        echo "[+] Installing Miniforge to $USER_HOME/miniforge3..."
        bash "$MINIFORGE_SH" -b -p "$USER_HOME/miniforge3"
        rm -f "$MINIFORGE_SH"
        
        "$USER_HOME/miniforge3/bin/mamba" init bash
        
        MAMBA_EXE="$USER_HOME/miniforge3/bin/mamba"
        echo "[+] Miniforge successfully installed!"
        echo "[!] NOTE: You may need to run 'source ~/.bashrc' after this script completes."
    else
        echo "[-] Error: Miniforge/Conda is required to manage ZebVR environments. Aborting installation."
        exit 1
    fi
fi

echo "[+] Using Miniforge binary: $MAMBA_EXE"


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
exec </dev/tty

if "$MAMBA_EXE" env list --json | grep -q "/$ENV_NAME\""; then
    echo "[!] Conda environment '$ENV_NAME' already exists."
    read -p "[?] Would you like to update/repair it using ZebVR.yml? (y/n): " update_env
    
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

# 7. Optional Hardware Component Installations
echo "-----------------------------------------"
echo "Optional Hardware Stack Configuration"
echo "-----------------------------------------"


# --- XIMEA Setup ---
read -p "[?] Do you want to install XIMEA Camera drivers & bindings? (y/n): " install_ximea
if [ "$install_ximea" = "y" ] || [ "$install_ximea" = "Y" ]; then
    echo "[+] Running XIMEA setup scripts..."
    "$MAMBA_EXE" run -n "$ENV_NAME" python scripts/setup_ximea.py
    
    if [ -f "install_ximea_systemd_service.sh" ]; then
        echo "[+] Configuring automated XIMEA systemd maintenance service..."
        chmod +x install_ximea_systemd_service.sh
        # Systemd service registration requires root privileges
        sudo ./install_ximea_systemd_service.sh
    else
        echo "[-] Warning: install_ximea_systemd_service.sh not found. Skipping service setup."
    fi
fi

# --- Aravis Setup ---
read -p "[?] Do you want to compile and install Aravis (GigE/USB3 cameras)? (y/n): " install_aravis
if [ "$install_aravis" = "y" ] || [ "$install_aravis" = "Y" ]; then
    echo "[+] Building Aravis from source..."
    CONDA_PREFIX_DIR=$("$MAMBA_EXE" run -n "$ENV_NAME" python -c "import os; print(os.environ['CONDA_PREFIX'])")
    
    git clone https://github.com/AravisProject/aravis.git
    cd aravis
    meson setup build --prefix="$CONDA_PREFIX_DIR" -Dintrospection=enabled -Dviewer=disabled -Dtests=true --libdir=lib
    ninja -C build install
    cd ..
    rm -rf aravis
    echo "[+] Aravis successfully compiled into active Conda environment."
fi

# --- Thorlabs Firmware ---
read -p "[?] Do you want to fetch Thorlabs Spectrophotometer firmware? (y/n): " install_thor
if [ "$install_thor" = "y" ] || [ "$install_thor" = "Y" ]; then
    echo "[+] Downloading Thorlabs firmware..."
    "$MAMBA_EXE" run -n "$ENV_NAME" python -m thorlabs_ccs.get_firmware
fi

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
Icon=$REPO_DIR/ZebVR/resources/zebvr.png
Terminal=true
Categories=Science;Education;Development;
EOF

# Make the desktop file executable
chmod +x "$DESKTOP_ENTRY_DIR/zebvr.desktop"
echo "[+] Desktop entry created! ZebVR will now show up in your system applications menu."

echo "=========================================================================="
echo "[+] SYSTEM INSTALLATION COMPLETE!"
echo "=========================================================================="
echo " IMPORTANT NEXT STEPS:"
echo " 1. You MUST log out and log back in (or reboot) for hardware group"
echo "    permissions (plugdev/dialout) to take effect."
echo " 2. If you installed XIMEA drivers, Secure Boot might need to be"
echo "    disabled in your system BIOS if the kernel module fails to load."
echo " 3. To activate this specific branch environment, run:"
echo "    val env: mamba activate $ENV_NAME"
echo "=========================================================================="