#!/bin/bash
if modprobe ximea_cam_pcie >/dev/null 2>&1; then
    echo "XIMEA driver is already loaded."
else
    echo "XIMEA driver missing. Rebuilding for $(uname -r)..."
    cd /opt/XIMEA/src/ximea_cam_pcie
    make clean && make KERNEL=$(uname -r) && make KERNEL=$(uname -r) install
    depmod -a
    modprobe ximea_cam_pcie
fi