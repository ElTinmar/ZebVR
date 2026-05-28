#!/bin/bash
set -e  

DRIVER_SRC="/opt/XIMEA/src/ximea_cam_pcie"

if modprobe ximea_cam_pcie >/dev/null 2>&1; then
    echo "XIMEA driver is already loaded."
    exit 0
fi

echo "XIMEA module missing. Checking source..."
if [ ! -d "$DRIVER_SRC" ]; then
    echo "ERROR: Source directory $DRIVER_SRC not found!" >&2
    echo "Please ensure the XIMEA SDK is installed correctly." >&2
    exit 1
fi

echo "Rebuilding for $(uname -r)..."
cd "$DRIVER_SRC"

if make clean && make KERNEL=$(uname -r) && make KERNEL=$(uname -r) install; then
    depmod -a
    modprobe ximea_cam_pcie
    echo "Driver successfully rebuilt and loaded."
else
    echo "ERROR: Build failed." >&2
    exit 1
fi
