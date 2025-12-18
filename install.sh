#!/bin/bash

echo "📺 Android TV Remote - Installer"
echo "==============================="

# Check for Python 3.11+
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed via 'python3'. Please install Python 3.11 or newer."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
     echo "❌ Python 3.11+ is required. Found version $PYTHON_VERSION"
     exit 1
fi

echo "✅ Python $PYTHON_VERSION found."

# Check for optional dependencies
echo "🔍 Checking optional dependencies..."

if command -v adb &> /dev/null; then
    echo "✅ ADB found (needed for optional advanced features)."
else
    echo "⚠️  ADB not found. Advanced features (Screen Mirroring, App Install) will be disabled."
    echo "   To install on Fedora: sudo dnf install android-tools"
    echo "   To install on Ubuntu/Debian: sudo apt install adb"
fi

if command -v scrcpy &> /dev/null; then
    echo "✅ scrcpy found (needed for Screen Mirroring)."
else
    echo "⚠️  scrcpy not found. Screen Mirroring will be disabled."
    echo "   To install on Fedora: sudo dnf install scrcpy"
    echo "   To install on Ubuntu/Debian: sudo apt install scrcpy"
fi

# Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and Install Local Package
source venv/bin/activate
echo "⬇️  Installing Android TV Remote and dependencies..."
pip install -e . --upgrade

# Create Desktop Entry
echo "📝 Creating desktop entry..."
PWD=$(pwd)
EXEC_PATH="$PWD/venv/bin/android-tv-remote"

cat > android-tv-remote.desktop << EOL
[Desktop Entry]
Name=Android TV Remote
Comment=Control your Android TV
Exec=$EXEC_PATH
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;Network;
EOL

chmod +x android-tv-remote.desktop

echo "==============================="
echo "✅ Installation Complete!"
echo "🚀 To run the app:"
echo "   source venv/bin/activate"
echo "   python tv_remote_app.py"
echo ""
echo "Or run the generated desktop file."
