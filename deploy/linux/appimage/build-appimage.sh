#!/bin/bash
set -e

APP_NAME="CampusConnect"
APP_DIR="AppDir"
APPIMAGE="CampusConnect-1.0.0-x86_64.AppImage"

echo "Building KyU Campus Connect AppImage..."

# Clean previous build
rm -rf "$APP_DIR" "$APPIMAGE"

# Create AppDir structure
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APP_DIR/opt/campus-connect"

# Copy application files
cp -r ../../backend "$APP_DIR/opt/campus-connect/"
cp -r ../../frontend "$APP_DIR/opt/campus-connect/"

# Create startup script
cat > "$APP_DIR/usr/bin/campus-connect" << 'EOF'
#!/bin/bash
INSTALL_DIR="/opt/campus-connect"
cd "$INSTALL_DIR"
source venv/bin/activate 2>/dev/null || true
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &
sleep 2
xdg-open http://localhost:8000
wait
EOF
chmod +x "$APP_DIR/usr/bin/campus-connect"

# Create desktop entry
cat > "$APP_DIR/usr/share/applications/campus-connect.desktop" << 'EOF'
[Desktop Entry]
Name=KyU Campus Connect
Comment=University Communication System
Exec=campus-connect
Icon=campus-connect
Terminal=true
Type=Application
Categories=Network;InstantMessaging;Education;
EOF

# Copy icon
cp ../../frontend/public/images/kyu-logo.png "$APP_DIR/usr/share/icons/hicolor/256x256/apps/campus-connect.png" 2>/dev/null || \
cp ../../frontend/public/images/kyu-logo.svg "$APP_DIR/usr/share/icons/hicolor/256x256/apps/campus-connect.svg" 2>/dev/null || true

# Create AppRun
cat > "$APP_DIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${HERE}/usr/sbin:${HERE}/usr/games:${HERE}/bin:${HERE}/sbin${PATH:+:$PATH}"
export PYTHONPATH="${HERE}/opt/campus-connect:${PYTHONPATH:+:$PYTHONPATH}"
exec "${HERE}/usr/bin/campus-connect" "$@"
EOF
chmod +x "$APP_DIR/AppRun"

# Build AppImage (requires appimagetool)
if command -v appimagetool &> /dev/null; then
    appimagetool "$APP_DIR" "$APPIMAGE"
    echo "AppImage built: $APPIMAGE"
else
    echo "appimagetool not found. Install with:"
    echo "  wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "  chmod +x appimagetool-x86_64.AppImage"
    echo "  sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool"
    echo ""
    echo "AppDir created at: $APP_DIR"
fi
