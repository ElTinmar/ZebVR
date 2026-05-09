#!/bin/bash

DRIVER_SRC="/opt/XIMEA/src/ximea_cam_pcie"

if modprobe ximea_cam_pcie >/dev/null 2>&1; then
    echo "XIMEA driver is already loaded."
else
    echo "XIMEA driver missing. Checking source..."
    
    if [ ! -d "$DRIVER_SRC" ]; then
        echo "ERROR: Source directory $DRIVER_SRC not found!"
        echo "Please ensure the XIMEA SDK is installed correctly."
        exit 1
    fi

    echo "Rebuilding for $(uname -r)..."
    cd "$DRIVER_SRC"
    
    if make clean && make KERNEL=$(uname -r) && make KERNEL=$(uname -r) install; then
        depmod -a
        modprobe ximea_cam_pcie
        echo "Driver successfully rebuilt and loaded."
    else
        echo "ERROR: Build failed. Check compiler and kernel headers."
        exit 1
    fi
fi