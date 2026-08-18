#!/bin/bash
set -e

echo "========================================="
echo " KyU Campus Connect - Linux Installer"
echo "========================================="
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./install.sh"
    exit 1
fi

# Install dependencies first (before dpkg)
echo "[1/4] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3-dev gcc libffi-dev build-essential python3-venv curl > /dev/null 2>&1

# Purge old install
echo "[2/4] Cleaning old installation..."
dpkg --purge campus-connect 2>/dev/null || true
rm -rf /opt/campus-connect /opt/campus-connect-temp

# Install package
echo "[3/4] Installing package..."
dpkg -i "$(dirname "$0")/build/campus-connect_1.0.0_amd64.deb"

echo "[4/4] Done!"
echo ""
echo "========================================="
echo " Installation Complete!"
echo "========================================="
echo ""
echo " Access: http://localhost:8000"
echo " Status: systemctl status campus-connect"
echo " Restart: systemctl restart campus-connect"
echo " Logs: journalctl -u campus-connect -f"
echo ""
