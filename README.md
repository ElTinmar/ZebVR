# ZebVR

Virtual reality for zebrafish.

<!---TODO
Add screenshots of the GUI
-->

## System requirements

This program has been tested on Ubuntu 24.04 with X11 (no Wayland support yet).
It should also run on Windows 10/11 but hasn't been extensively tested, and full
installation instructions on Windows are not listed here.
We recommend using a modern multicore machine with at least 32GB of RAM.
Parts of the installation process require sudo rights.

## Extra Hardware (optional)

- ViewSonic X2-4K projector
- Thorlabs PM100D
- Thorlabs CCS100

For a full list of hardware used for the VR setup, see doc/BOM/bom.md

## Software dependencies

### deb packages on Ubuntu

```bash
sudo apt-get install libportaudio2 build-essential libusb-1.0-0-dev 
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
conda env create -f ZebVR3.yml
conda activate ZebVR3
```

A full list of dependencies with version number can be found in requirements.txt

### Install camera SDK and python bindings into environment

The SDK and python binding URLs are hardcoded in the script and will break
if the camera manufacturers decide to change their website layout. The SDK 
can be manually downloaded from the manufacturer website, and the python module placed
in the conda environment site-packages folder (e.g. /home/user/miniconda3/envs/ZebVR3/lib/python3.13/site-packages/ximea)

```bash
conda activate ZebVR3
python setup_ximea.py
python setup_spinnaker.py
```

You can also install the SDK (requires sudo) or python bindings separately:

```bash
python setup_ximea.py --only-sdk
python setup_spinnaker.py --only-sdk
```

```bash
conda activate ZebVR3
python setup_ximea.py --only-python
python setup_spinnaker.py --only-python
```

Please note that every time a new kernel is installed during a system update,
the SDK needs to be reinstalled.

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
conda activate ZebVR3
python -m ZebVR
```

## Demo

This is virtual reality program and is meant to be run with a camera input.
However, for demonstration/testing purposes, the program can be run using a video file as input:


In the camera tab, select `MOVIE` in the dropdown menu, then click on `Load file`
An example movie is provided in `example/4_fish.mp4`

## Troubleshooting

### PCIe Camera No LED 

Make sure the power switch on the PCIe adapapter board is on 24V

### Ximea Error 57

if error 57 device already open, or if program is slower than usual

```bash
sudo killall python
```

### Ximea Error 56

if error 56 No Devices Found, reinstall SDK (requires sudo)

```bash
python setup_ximea.py --only-sdk
```

### libtiff.so.5: cannot open shared object file

```
sudo apt install libtiff6
cd /usr/lib/x86_64-linux-gnu/
sudo ln -s libtiff.so.6 libtiff.so.5
```

### modprobe: ERROR: could not insert 'ximea_cam_pcie': Key was rejected by service

Disable secure boot in the BIOS

### module not found

Try refreshing the environment

```
conda env update -f ZebVR3.yml
```