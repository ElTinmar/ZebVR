#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================="
echo "       ZebVR Installation Script        "
echo "========================================="

# 1. Check for Sudo / Root Permissions up front
if [ "$EUID" -ne 0 ]; then
  echo "[-] Error: Please run this script with sudo or as root:"
  echo "    sudo ./install.sh"
  exit 1
fi

# Store the actual user who invoked sudo and their home directory
REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$REAL_USER)

# 2. Install Core System Dependencies via apt
echo "[+] Installing system dependencies..."
apt-get update
apt-get install -y libportaudio2 build-essential libusb-1.0-0-dev innoextract curl

# 3. Labjack Exodriver Setup
echo "[+] Checking Labjack Exodriver..."
if [ -f "/usr/local/lib/liblabjackusb.so" ] || [ -f "/usr/lib/liblabjackusb.so" ]; then
    echo "[+] Labjack Exodriver is already installed. Skipping compilation."
else
    echo "[+] Labjack Exodriver not found. Installing from source..."
    if [ ! -d "exodriver" ]; then
        sudo -u "$REAL_USER" git clone https://github.com/labjack/exodriver.git
    fi
    cd exodriver
    ./install.sh
    cd ..
    rm -rf exodriver
    echo "[+] Labjack Exodriver successfully installed."
fi

# 4. Hardware Permissions & Udev Rules
echo "[+] Adding '$REAL_USER' to plugdev and dialout groups..."
usermod -a -G plugdev,dialout "$REAL_USER"

echo "[+] Writing Thorlabs udev rules..."
cat << 'EOF' > /etc/udev/rules.d/99-thorlabs.rules
SUBSYSTEMS=="usb", ATTRS{idVendor}=="1313", GROUP="plugdev", MODE="0666"
EOF

echo "[+] Reloading udev rules..."
udevadm control --reload-rules
udevadm trigger


# 5. Locate or Install Conda
echo "[+] Locating Conda installation..."
CONDA_EXE=""

# Method A: Check the user's environment variable via login shell (mute stderr)
if [ -z "$CONDA_EXE" ]; then
    CONDA_EXE=$(sudo -u "$REAL_USER" -i bash -c 'echo $CONDA_EXE' 2>/dev/null || true)
fi

# Method B: Use 'command -v' instead of 'which' to prevent set -e crashes
if [ -z "$CONDA_EXE" ]; then
    USER_WHICH=$(sudo -u "$REAL_USER" -i bash -c 'command -v conda' 2>/dev/null || true)
    if [ -n "$USER_WHICH" ] && [ -f "$USER_WHICH" ]; then
        CONDA_EXE="$USER_WHICH"
    fi
fi

# Method C: Check standard absolute default fallback locations
if [ -z "$CONDA_EXE" ]; then
    if [ -f "$USER_HOME/miniconda3/bin/conda" ]; then
        CONDA_EXE="$USER_HOME/miniconda3/bin/conda"
    elif [ -f "$USER_HOME/anaconda3/bin/conda" ]; then
        CONDA_EXE="$USER_HOME/anaconda3/bin/conda"
    fi
fi

# Method D: If Conda is completely missing, offer to install Miniconda automatically
if [ -z "$CONDA_EXE" ] || [ ! -f "$CONDA_EXE" ]; then
    echo "[-] Conda was not found on this system."
    # Redirecting to /dev/tty guarantees the prompt shows up even during weird piping
    exec </dev/tty
    read -p "[?] Would you like to automatically download and install Miniconda3 for $REAL_USER? (y/n): " install_conda
    
    if [ "$install_conda" = "y" ] || [ "$install_conda" = "Y" ]; then
        echo "[+] Downloading Miniconda installer..."
        MINICONDA_SH="/tmp/Miniconda3-latest-Linux-x86_64.sh"
        
        sudo -u "$REAL_USER" curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o "$MINICONDA_SH"
        
        echo "[+] Installing Miniconda to $USER_HOME/miniconda3..."
        sudo -u "$REAL_USER" bash "$MINICONDA_SH" -b -p "$USER_HOME/miniconda3"
        rm -f "$MINICONDA_SH"
        
        sudo -u "$REAL_USER" "$USER_HOME/miniconda3/bin/conda" init bash
        
        CONDA_EXE="$USER_HOME/miniconda3/bin/conda"
        echo "[+] Miniconda successfully installed!"
    else
        echo "[-] Error: Conda is required to manage ZebVR environments. Aborting installation."
        exit 1
    fi
fi

echo "[+] Using Conda binary: $CONDA_EXE"

if "$CONDA_EXE" env list | grep -q "ZebVR"; then
    echo "[+] Conda environment 'ZebVR' already exists. Updating it..."
    sudo -u "$REAL_USER" CONDA_CONDARC_D="" "$CONDA_EXE" env update -f ZebVR.yml --prune
else
    echo "[+] Creating ZebVR Conda environment from ZebVR.yml..."
    # This completely isolates the creation command from the host's global ~/.condarc
    sudo -u "$REAL_USER" CONDA_CONDARC_D="" "$CONDA_EXE" env create -f ZebVR.yml --yes
fi

# 7. Optional Hardware Component Installations
echo "-----------------------------------------"
echo "Optional Hardware Stack Configuration"
echo "-----------------------------------------"
exec </dev/tty

# --- XIMEA Setup ---
read -p "[?] Do you want to install XIMEA Camera drivers & bindings? (y/n): " install_ximea
if [ "$install_ximea" = "y" ] || [ "$install_ximea" = "Y" ]; then
    echo "[+] Running XIMEA setup scripts..."
    sudo -u "$REAL_USER" "$CONDA_EXE" run -n ZebVR python scripts/setup_ximea.py
    sudo -u "$REAL_USER" "$CONDA_EXE" run -n ZebVR python scripts/setup_spinnaker.py
    
    if [ -f "install_ximea_systemd_service.sh" ]; then
        echo "[+] Configuring automated XIMEA systemd maintenance service..."
        chmod +x install_ximea_systemd_service.sh
        ./install_ximea_systemd_service.sh
    else
        echo "[-] Warning: install_ximea_systemd_service.sh not found. Skipping service setup."
    fi
fi

# --- Aravis Setup ---
read -p "[?] Do you want to compile and install Aravis (GigE/USB3 cameras)? (y/n): " install_aravis
if [ "$install_aravis" = "y" ] || [ "$install_aravis" = "Y" ]; then
    echo "[+] Building Aravis from source..."
    CONDA_PREFIX_DIR=$(sudo -u "$REAL_USER" "$CONDA_EXE" run -n ZebVR python -c "import os; print(os.environ['CONDA_PREFIX'])")
    
    sudo -u "$REAL_USER" git clone https://github.com/AravisProject/aravis.git
    cd aravis
    sudo -u "$REAL_USER" meson setup build --prefix="$CONDA_PREFIX_DIR" -Dintrospection=enabled -Dviewer=disabled -Dtests=true --libdir=lib
    sudo -u "$REAL_USER" ninja -C build install
    cd ..
    rm -rf aravis
    echo "[+] Aravis successfully compiled into active Conda environment."
fi

# --- Thorlabs Firmware ---
read -p "[?] Do you want to fetch Thorlabs Spectrophotometer firmware? (y/n): " install_thor
if [ "$install_thor" = "y" ] || [ "$install_thor" = "Y" ]; then
    echo "[+] Downloading Thorlabs firmware..."
    sudo -u "$REAL_USER" "$CONDA_EXE" run -n ZebVR python -m thorlabs_ccs.get_firmware
fi

echo "=========================================================================="
echo "[+] SYSTEM INSTALLATION COMPLETE!"
echo "=========================================================================="
echo " IMPORTANT NEXT STEPS:"
echo " 1. You MUST log out and log back in (or reboot) for hardware group"
echo "    permissions (plugdev/dialout) to take effect."
echo " 2. If you installed XIMEA drivers, Secure Boot might need to be"
echo "    disabled in your system BIOS if the kernel module fails to load."
echo "=========================================================================="