#!/bin/bash
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (use sudo)"
  exit
fi

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

mkdir -p /usr/local/bin
cp "$REPO_DIR/scripts/ximea_fix_driver.sh" /usr/local/bin/ximea_fix_driver.sh
chmod +x /usr/local/bin/ximea_fix_driver.sh
cp "$REPO_DIR/scripts/ximea_systemd.service" /etc/systemd/system/ximea-startup.service

# Activate service
systemctl daemon-reload
systemctl enable ximea-startup.service
systemctl start ximea-startup.service

echo "-------------------------------------------------------"
echo "XIMEA Auto-Maintenance Service Installed successfully."
echo "The driver will be verified and rebuilt automatically at boot."
echo "Check status with: systemctl status ximea-startup.service"
echo "-------------------------------------------------------"