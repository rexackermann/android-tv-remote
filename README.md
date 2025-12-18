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

### 2. Install
Run the included installation script:

```bash
chmod +x install.sh
./install.sh
```

## Usage

### Launching the App
You can launch the app from your application menu ("Android TV Remote") or via command line:

```bash
source venv/bin/activate
python tv_remote_app.py
```

### Connecting to a TV
1. On the **Devices** tab, wait for your TV to appear in the list (or click **Refresh**).
2. Double-click your TV to connect.
3. If this is your first time, click **Start Pairing**.
4. A pairing code will appear on your TV screen.
5. Enter the code in the **Pairing Code** field in the app and click **Verify**.

### Controls
- **Remote Tab**: Standard navigation buttons.
- **Touchpad Area**:
    - **Tap**: OK / Select
    - **Swipe**: Navigation (Up/Down/Left/Right)
    - **Right Click**: Back
- **Keyboard**: Go to "Features" tab to send text input.

### Screen Mirroring
1. Go to the **Features** tab.
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
