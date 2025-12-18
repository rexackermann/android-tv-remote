#!/bin/bash

# Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "📺 Android TV Remote - System Installer"
echo "======================================="

INSTALL_DIR="/opt/android-tv-remote"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"

# clean previous install
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

echo "📂 Copying files to $INSTALL_DIR..."
# Copy current directory contents to install dir, excluding venv/git/etc
rsync -av --progress . "$INSTALL_DIR" --exclude venv --exclude .git --exclude __pycache__ --exclude .config

echo "📦 Creating virtual environment in $INSTALL_DIR/venv..."
python3 -m venv "$INSTALL_DIR/venv"

echo "⬇️  Installing dependencies..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install "$INSTALL_DIR"

echo "🔗 Creating symlink..."
ln -sf "$INSTALL_DIR/venv/bin/android-tv-remote" "$BIN_DIR/android-tv-remote"

echo "📝 Installing desktop entry..."
# Update desktop file to point to the correct icon if we had one, 
# for now we stick to system icon 'utilities-terminal' or generic.
# We need to make sure the Exec path is just the command name since it's in /usr/local/bin
sed -i 's|^Exec=.*|Exec=android-tv-remote|' android-tv-remote.desktop

cp android-tv-remote.desktop "$DESKTOP_DIR/"
chmod 644 "$DESKTOP_DIR/android-tv-remote.desktop"

echo "======================================="
echo "✅ Installation Complete!"
echo "   App installed to: $INSTALL_DIR"
echo "   Command available globally: android-tv-remote"
echo "   Desktop entry installed."
echo ""
echo "🚀 You can now delete the source folder if you wish."

