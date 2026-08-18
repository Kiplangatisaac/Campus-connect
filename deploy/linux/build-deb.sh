#!/bin/bash
set -e

echo "Building KyU Campus Connect .deb package..."

# Clean previous build
rm -rf build/
mkdir -p build/campus-connect_1.0.0_amd64

# Copy package structure
cp -r DEBIAN build/campus-connect_1.0.0_amd64/
cp -r opt build/campus-connect_1.0.0_amd64/ 2>/dev/null || true
cp -r usr build/campus-connect_1.0.0_amd64/ 2>/dev/null || true

# Copy application files
mkdir -p build/campus-connect_1.0.0_amd64/opt/campus-connect-temp
cp -r ../../backend build/campus-connect_1.0.0_amd64/opt/campus-connect-temp/
cp -r ../../frontend build/campus-connect_1.0.0_amd64/opt/campus-connect-temp/

# Build package
dpkg-deb --build build/campus-connect_1.0.0_amd64

echo "Package built: build/campus-connect_1.0.0_amd64.deb"
echo "Install with: sudo dpkg -i build/campus-connect_1.0.0_amd64.deb"
