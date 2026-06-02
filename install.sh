#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================="
echo "       ZebVR Installation Script        "
echo "========================================="

# 1. Check for Sudo / Root Permissions up front
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo or as root:"
  echo "sudo ./install.sh"
  exit 1
fi

# Store the actual user who invoked sudo
REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$REAL_USER)

echo "Installing system dependencies..."
apt-get update
apt-get install -y libportaudio2 build-essential libusb-1.0-0-dev innoextract

# 2. Labjack Exodriver Setup
echo "Installing Labjack Exodriver..."
if [ ! -d "exodriver" ]; then
    git clone https://github.com/labjack/exodriver.git
fi
cd exodriver
./install.sh
cd ..
rm -rf exodriver

# 3. Hardware Permissions & Udev Rules
echo "Setting up hardware permissions and udev rules..."
usermod -a -G plugdev,dialout "$REAL_USER"

cat << 'EOF' > /etc/udev/rules.d/99-thorlabs.rules
SUBSYSTEMS=="usb", ATTRS{idVendor}=="1313", GROUP="plugdev", MODE="0666"
EOF

udevadm control --reload-rules
udevadm trigger

# 4. Conda Environment Setup (Run as the actual user, not root)
echo "Setting up Conda environment for user: $REAL_USER..."
# Locate conda executable dynamically if possible, or assume default paths
export -f -n conda # clears functions
if [ -f "$USER_HOME/miniconda3/bin/conda" ]; then
    CONDA_PATH="$USER_HOME/miniconda3/bin/conda"
elif [ -f "$USER_HOME/anaconda3/bin/conda" ]; then
    CONDA_PATH="$USER_HOME/anaconda3/bin/conda"
else
    read -p "Conda not found in default paths. Please enter the path to your 'conda' executable: " CONDA_PATH
fi

# Create env as the real user
sudo -u "$REAL_USER" "$CONDA_PATH" env create -f ZebVR.yml --yes || true

# 5. Hardware-Specific Prompting (Optional Components)
echo "-----------------------------------------"
read -p "Do you want to install XIMEA Camera drivers? (y/n): " install_ximea
if [ "$install_ximea" = "y" ] || [ "$install_ximea" = "Y" ]; then
    sudo -u "$REAL_USER" "$CONDA_PATH" run -n ZebVR python scripts/setup_ximea.py
    # Install automated service
    chmod +x install_ximea_systemd_service.sh
    ./install_ximea_systemd_service.sh
fi

read -p "Do you want to install Aravis (GigE/USB3 cameras)? (y/n): " install_aravis
if [ "$install_aravis" = "y" ] || [ "$install_aravis" = "Y" ]; then
    CONDA_PREFIX_DIR=$(sudo -u "$REAL_USER" "$CONDA_PATH" run -n ZebVR python -c "import os; print(os.environ['CONDA_PREFIX'])")
    sudo -u "$REAL_USER" git clone https://github.com/AravisProject/aravis.git
    cd aravis
    sudo -u "$REAL_USER" meson setup build --prefix="$CONDA_PREFIX_DIR" -Dintrospection=enabled -Dviewer=disabled -Dtests=true --libdir=lib
    sudo -u "$REAL_USER" ninja -C build install
    cd ..
    rm -rf aravis
fi

read -p "Do you want to fetch Thorlabs firmware? (y/n): " install_thor
if [ "$install_thor" = "y" ] || [ "$install_thor" = "Y" ]; then
    sudo -u "$REAL_USER" "$CONDA_PATH" run -n ZebVR python -m thorlabs_ccs.get_firmware
fi

echo "========================================="
echo "Installation complete! Please REBOOT your machine to apply group permissions."
echo "========================================="