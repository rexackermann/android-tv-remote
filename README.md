# Android TV Remote for Linux

A premium, touch-first Android TV remote control application for Linux desktops. Features kinetic scrolling, multi-dimensional touchpad physics, real-time keyboard input, and screen mirroring.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-blue.svg)
![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-green.svg)

## Features

- **Wi-Fi Remote Control**: Uses the official Google TV protocol (fast, reliable, no ADB required for basic control).
- **Physics-Based Touchpad**: "Sticky" touchpad with distance-weighted acceleration and directional reset physics.
- **Kinetic Scrolling**: Native flick-to-scroll experience for remote buttons.
- **Smart Keyboard**: Type directly on your TV from your PC (supports real-time sync).
- **Screen Mirroring**: Integrated low-latency mirroring via `scrcpy`.
- **Auto-Discovery**: Zero-configuration device finding on your local network.

## Dependencies

Before installing, ensure you have the required system dependencies found on your distribution.

### Fedora
```bash
sudo dnf install python3-devel android-tools scrcpy
```

### Ubuntu / Debian
```bash
sudo apt install python3-dev android-tools-adb scrcpy
```

### Arch Linux
```bash
sudo pacman -S python android-tools scrcpy
```

*> Note: `scrcpy` and `android-tools` are optional but required if you want to use Screen Mirroring.*

## Installation (System-Wide)

To install the application globally on your system:

1.  **Clone the repository** (or download source):
    ```bash
    git clone https://github.com/rexackermann/android-tv-remote.git
    cd android-tv-remote
    ```

2.  **Run the installer**:
    ```bash
    chmod +x install.sh
    sudo ./install.sh
    ```

This ensures a clean installation to `/opt/android-tv-remote` and creates a global entry point. The source folder can be safely deleted after installation.

## Usage

### Launching
- **GUI**: Open your application menu and search for **"Android TV Remote"**.
- **Terminal**: Run `android-tv-remote`.

### Controls
- **Remote Tab**:
    - **Buttons**: Click or use "Flick" gestures to scroll deeply.
    - **Touchpad**:
        - **Tap**: OK / Select.
        - **Swipe**: Navigate (Up/Down/Left/Right).
        - **Hold**: "Turbo" repeat mode.
        - **Pull Further**: Increases scroll speed (Joystick physics).
        - **Right Click**: Back.

### Settings & Mirroring
- **Pairing**: Automatically handles pairing codes on first connection.
- **Mirroring**: Enable in the **Settings** tab. Requires ADB debugging enabled on the TV.

## Updating

To update the application to the latest version:

1.  Pull the latest changes:
    ```bash
    git pull
    ```
2.  Re-run the installer:
    ```bash
    sudo ./install.sh
    ```

## Uninstallation

To completely remove the application from your system:

```bash
# 1. Remove application files
sudo rm -rf /opt/android-tv-remote

# 2. Remove binary symlink
sudo rm /usr/local/bin/android-tv-remote

# 3. Remove desktop entry
sudo rm /usr/share/applications/android-tv-remote.desktop
```

*> User configuration and keys stored in `~/.config/android-tv-remote/` are preserved. Delete that folder manually if you want a full wipe.*

## Privacy & Data Storage

This application respects your privacy.

- **Repository**: The source code repository is **clean**. It does not store or track any personal IP addresses, certificates, or keys.
- **Local Config**: All sensitive data (paired device certificates, last connected IP) is stored locally on your machine at:
    ```
    ~/.config/android-tv-remote/
    ```
- **Network**: The app communicates ONLY with devices on your local network. No data is sent to external cloud servers.

## Troubleshooting

- **"Device not found"**: Ensure both PC and TV are on the same Wi-Fi. Check firewall settings.
- **"Pairing Failed"**: Remove any "Linux TV Remote" entries from your TV's *Settings -> Remotes & Accessories* menu and try again.
- **"Mirroring Failed"**: Running `scrcpy` manually in a terminal often reveals the error (usually unauthorized ADB state).

## License

MIT License

Copyright (c) 2025 **Rex Ackermann**

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
