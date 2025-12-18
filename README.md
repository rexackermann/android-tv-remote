# Android TV Remote for Linux

Control your Android TV from your Linux desktop with keyboard, touchpad, and screen mirroring support.

## Features

- **Wi-Fi Remote Control**: Uses the official Google TV protocol (no ADB required for basic control).
- **Touchpad Support**: Control your TV navigation with a laptop touchpad or mouse gestures.
- **Keyboard Input**: Type on your TV using your computer keyboard.
- **Screen Mirroring**: View your TV screen on your PC (Requires ADB).
- **Auto-Discovery**: Automatically finds Android TVs on your local network.

## Installation

### 1. Prerequisites
- **Python 3.11+**
- **Fedora**: `sudo dnf install python3-devel android-tools scrcpy`
- **Ubuntu/Debian**: `sudo apt install python3-dev android-tools-adb scrcpy`
- *Note: `scrcpy` and `android-tools` are only required if you want Screen Mirroring features.*

### 2. Install (System-Wide)
Run the included installation script as root:

```bash
chmod +x install.sh
sudo ./install.sh
```

This will:
- Install the application to `/opt/android-tv-remote`
- Create a global command `android-tv-remote`
- Install a desktop entry for your application menu

## Usage

### Launching the App
Arguments:
- **Terminal**: Type `android-tv-remote` anywhere.
- **GUI**: Search for "Android TV Remote" in your application menu.

### Connecting to a TV
1. On the **Devices** tab, wait for your TV to appear in the list (or click **Refresh**).
2. Double-click your TV to connect.
3. If this is your first time, click **Start Pairing**.
4. A pairing code will appear on your TV screen.
5. Enter the code in the **Pairing Code** field in the app and click **Verify**.

### Controls
- **Remote Tab**: Standard navigation buttons with **Kinetic Scrolling**.
- **Touchpad Area (Sticky)**:
    - **Tap**: OK / Select
    - **Swipe**: Navigation (Up/Down/Left/Right) - *Faster swipes accelerate navigation!*
    - **Right Click**: Back
    - **Hold**: Continuous repeat (like a joystick)
- **Settings**: Configure mirroring and keyboard input.

### Screen Mirroring
1. Go to the **Settings** tab.
2. Ensure connection is active.
3. Check **Enable Mirroring**.
   - *Requirement*: You must have ADB Debugging enabled on your Android TV settings (Developer Options).

## Troubleshooting

- **Device not found**: Ensure PC and TV are on the same Wi-Fi network. Try "Connect via IP" if auto-discovery fails.
- **Pairing fails**: Check if "Linux TV Remote" is already in your TV's "Connected Devices" list and remove it to restart pairing.
- **Mirroring doesn't start**:
    - Verify ADB is installed (`adb version`).
    - Verify Scrcpy is installed (`scrcpy --version`).
    - Check if ADB debugging is enabled on the TV.

## License

MIT License

Copyright (c) 2025 **Rex Ackermann**

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
