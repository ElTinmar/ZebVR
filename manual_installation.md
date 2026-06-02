## Software dependencies

### deb packages on Ubuntu

```bash
sudo apt-get install libportaudio2 build-essential libusb-1.0-0-dev git
```

### Labjack exodriver

On Ubuntu:
```bash
git clone https://github.com/labjack/exodriver.git
cd exodriver/
sudo ./install.sh
cd .. 
rm -rf exodriver
```

Windows: https://files.labjack.com/installers/LJM/Windows/x86_64/release/LabJack_2024-05-16.exe

## Installation instructions

Solving the environment might take a few minutes.

```bash
git clone https://github.com/ElTinmar/ZebVR.git
cd ZebVR
conda env create -f ZebVR.yml
conda activate ZebVR
```

A full list of dependencies with version number can be found in requirements.txt

### Install camera SDK and python bindings into environment

#### XIMEA

The SDK and python binding URLs are hardcoded in the script and will break
if the camera manufacturers decide to change their website layout. The SDK 
can be manually downloaded from the manufacturer website, and the python module placed
in the conda environment site-packages folder (e.g. /home/user/miniconda3/envs/ZebVR/lib/python3.13/site-packages/ximea)

```bash
conda activate ZebVR
python scripts/setup_ximea.py
python scripts/setup_spinnaker.py
```

You can also install the SDK (requires sudo) or python bindings separately:

```bash
python scripts/setup_ximea.py --only-sdk
python scripts/setup_spinnaker.py --only-sdk
```

```bash
conda activate ZebVR
python scripts/setup_ximea.py --only-python
python scripts/setup_spinnaker.py --only-python
```

Please note that every time a new kernel is installed during a system update,
the SDK needs to be reinstalled.

##### Automated XIMEA Driver Maintenance

After the drivers have been installed once (see steps above), to prevent the XIMEA camera driver from breaking during Ubuntu kernel updates, 
install the automated maintenance service:

```bash
sudo chmod +x install_ximea_systemd_service.sh
sudo ./install_ximea_systemd_service.sh
```

Secure boot might need to be disabled.

#### Aravis

```bash
conda activate ZebVR
git clone https://github.com/AravisProject/aravis.git
cd aravis 
meson setup build --prefix=$CONDA_PREFIX -Dintrospection=enabled -Dviewer=disabled -Dtests=true --libdir=lib
ninja -C build install
cd ..
rm -rf aravis
```

### Thorlabs hardware 

This is needed to communicate with Thorlabs spectrophotometer and power measurement unit 
for automated power measurements.

```bash
sudo apt install innoextract
python -m thorlabs_ccs.get_firmware
```

set udev rule for all Thorlabs devices:

```bash
sudo tee /etc/udev/rules.d/99-thorlabs.rules > /dev/null << 'EOF'
SUBSYSTEMS=="usb", ATTRS{idVendor}=="1313", GROUP="plugdev", MODE="0666"
EOF
```

Reload udev rules:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Permissions to access hardware

```bash
sudo usermod -a -G plugdev,dialout "$USER"
```

## Running the software 

```bash
conda activate ZebVR
python -m ZebVR
```
