import sys
import asyncio
import logging
from typing import Optional
import qasync
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QListWidget, 
                            QMessageBox, QInputDialog, QLineEdit, QGroupBox,
                            QTabWidget, QCheckBox, QStatusBar, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QKeyEvent, QColor, QBrush, QLinearGradient

from config import cfg
from android_tv_controller import AndroidTVController
from device_discovery import DeviceDiscovery
from adb_controller import ADBController
from scrcpy_manager import ScrcpyManager
from touchpad_widget import TouchpadWidget

logger = logging.getLogger(__name__)

class AndroidTVRemoteApp(QMainWindow):
    # Signals for thread-safe UI updates from discovery thread
    device_found_sig = pyqtSignal(dict)
    device_lost_sig = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Android TV Remote (Linux)")
        self.resize(400, 700)
        
        # Controllers
        self.tv_controller = AndroidTVController()
        self.adb_controller = ADBController()
        self.scrcpy_manager = ScrcpyManager()
        self.discovery = DeviceDiscovery(self.on_device_found, self.on_device_lost)

        # Connect Signals
        self.device_found_sig.connect(self._add_device_sub)
        self.device_lost_sig.connect(self._remove_device_sub)

        # UI Setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.setup_ui()
        self.setup_callbacks()
        
        # Start Discovery
        self.discovery.start_discovery()
        
        # Auto-connect to last device
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Use singleShot to ensure UI is ready before auto-connect
        QTimer.singleShot(100, self.auto_connect_startup)

    def auto_connect_startup(self):
        last_ip = cfg.get("last_connected_device_ip")
        if last_ip:
            self.tabs.setCurrentIndex(1) # Start on Remote tab
            self.update_status(f"Auto-connecting to {last_ip}...")
            asyncio.create_task(self._perform_connect(last_ip))
        else:
            self.update_status("Scanning for devices...")

    def setup_ui(self):
        # Tabs: Remote | Devices | Settings
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # -- DEVICES TAB --
        self.devices_tab = QWidget()
        dev_layout = QVBoxLayout(self.devices_tab)
        
        self.device_list_widget = QListWidget()
        self.device_list_widget.itemDoubleClicked.connect(self.connect_to_selected_device)
        
        dev_list_header = QHBoxLayout()
        dev_list_header.addWidget(QLabel("Available Devices:"))
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setFixedWidth(80)
        btn_refresh.clicked.connect(self.refresh_discovery)
        dev_list_header.addWidget(btn_refresh)
        
        dev_layout.addLayout(dev_list_header)
        dev_layout.addWidget(self.device_list_widget)
        
        btn_layout = QHBoxLayout()
        btn_connect_manual = QPushButton("Connect via IP")
        btn_connect_manual.clicked.connect(self.manual_connect_dialog)
        btn_layout.addWidget(btn_connect_manual)

        btn_repair = QPushButton("Force Re-pair")
        btn_repair.clicked.connect(self.repair_selected_device)
        btn_layout.addWidget(btn_repair)
        dev_layout.addLayout(btn_layout)

        # Simplified Pairing Input (Hidden by default, used via dialog)
        self.txt_pairing_code = QLineEdit()
        self.txt_pairing_code.hide() 
        
        self.tabs.addTab(self.devices_tab, "Devices")
        
        # -- REMOTE TAB (Wrapped in ScrollArea) --
        self.remote_scroll = QScrollArea()
        self.remote_scroll.setWidgetResizable(True)
        self.remote_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.remote_scroll.setStyleSheet("background: transparent;")
        
        self.remote_tab = QWidget()
        self.remote_tab.setObjectName("remote_tab")
        self.remote_scroll.setWidget(self.remote_tab)
        
        remote_layout = QVBoxLayout(self.remote_tab)
        remote_layout.setContentsMargins(10, 10, 10, 10)
        remote_layout.setSpacing(15)
        
        # D-pad Config
        nav_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout(nav_group)
        
        from PyQt6.QtWidgets import QGridLayout
        dpad_grid = QGridLayout()
        dpad_grid.setSpacing(10)
        
        btn_up = QPushButton("▲")
        btn_down = QPushButton("▼")
        btn_left = QPushButton("◀")
        btn_right = QPushButton("▶")
        btn_center = QPushButton("OK")
        btn_center.setObjectName("btn_center")
        btn_center.setProperty("class", "accent")
        
        for btn in [btn_up, btn_down, btn_left, btn_right, btn_center]:
            btn.setFixedSize(65, 65)
            btn.setFont(QFont("Inter", 16, QFont.Weight.Bold))
            
        dpad_grid.addWidget(btn_up, 0, 1)
        dpad_grid.addWidget(btn_left, 1, 0)
        dpad_grid.addWidget(btn_center, 1, 1)
        dpad_grid.addWidget(btn_right, 1, 2)
        dpad_grid.addWidget(btn_down, 2, 1)
        
        container = QWidget()
        container.setLayout(dpad_grid)
        nav_layout.addWidget(container, 0, Qt.AlignmentFlag.AlignCenter)
        remote_layout.addWidget(nav_group)
        
        # Connect buttons
        btn_up.clicked.connect(lambda: self.tv_controller.send_key("DPAD_UP"))
        btn_down.clicked.connect(lambda: self.tv_controller.send_key("DPAD_DOWN"))
        btn_left.clicked.connect(lambda: self.tv_controller.send_key("DPAD_LEFT"))
        btn_right.clicked.connect(lambda: self.tv_controller.send_key("DPAD_RIGHT"))
        btn_center.clicked.connect(lambda: self.tv_controller.send_key("DPAD_CENTER"))

        # Function Buttons
        func_layout = QHBoxLayout()
        btn_back = QPushButton("Back")
        btn_home = QPushButton("Home")
        btn_menu = QPushButton("Menu")  # Often 'SETTINGS' or 'MENU'
        
        btn_back.clicked.connect(lambda: self.tv_controller.send_key("BACK"))
        btn_home.clicked.connect(lambda: self.tv_controller.send_key("HOME"))
        btn_menu.clicked.connect(lambda: self.tv_controller.send_key("SETTINGS"))

        func_layout.addWidget(btn_back)
        func_layout.addWidget(btn_home)
        func_layout.addWidget(btn_menu)
        remote_layout.addLayout(func_layout)
        
        # Power & Channel
        pc_layout = QHBoxLayout()
        btn_power = QPushButton("POWER")
        btn_power.setObjectName("btn_power") 
        btn_chup = QPushButton("CH +")
        btn_chdown = QPushButton("CH -")
        
        btn_power.clicked.connect(lambda: self.tv_controller.send_key("POWER"))
        btn_chup.clicked.connect(lambda: self.tv_controller.send_key("PAGE_UP"))   # Often CH+
        btn_chdown.clicked.connect(lambda: self.tv_controller.send_key("PAGE_DOWN")) # Often CH-
        
        pc_layout.addWidget(btn_power)
        pc_layout.addWidget(btn_chup)
        pc_layout.addWidget(btn_chdown)
        remote_layout.addLayout(pc_layout)
        
        # Volume
        vol_layout = QHBoxLayout()
        btn_voldown = QPushButton("Vol -")
        btn_mute = QPushButton("Mute")
        btn_volup = QPushButton("Vol +")
        
        btn_voldown.clicked.connect(lambda: self.tv_controller.send_key("VOLUME_DOWN"))
        btn_mute.clicked.connect(lambda: self.tv_controller.send_key("MUTE"))
        btn_volup.clicked.connect(lambda: self.tv_controller.send_key("VOLUME_UP"))
        
        vol_layout.addWidget(btn_voldown)
        vol_layout.addWidget(btn_mute)
        vol_layout.addWidget(btn_volup)
        remote_layout.addWidget(QLabel("Volume"))
        remote_layout.addLayout(vol_layout)
        
        # Media Controls
        media_group = QGroupBox("Media")
        media_layout = QVBoxLayout(media_group)
        
        row_media1 = QHBoxLayout()
        btn_prev = QPushButton("⏮")
        btn_rew = QPushButton(" << ")
        btn_play = QPushButton("▶")
        btn_pause = QPushButton("Ⅱ")
        btn_ff = QPushButton(" >> ")
        btn_next = QPushButton("⏭")
        
        for btn in [btn_prev, btn_rew, btn_play, btn_pause, btn_ff, btn_next]:
            btn.setFixedSize(50, 45) # Slightly larger for better touch/click targets
            btn.setFont(QFont("Inter", 12, QFont.Weight.Bold))
            
        btn_prev.clicked.connect(lambda: self.tv_controller.send_key("MEDIA_PREVIOUS"))
        btn_rew.clicked.connect(lambda: self.tv_controller.send_key("MEDIA_REWIND"))
        btn_play.clicked.connect(lambda: self.tv_controller.send_key("MEDIA_PLAY"))
        btn_pause.clicked.connect(lambda: self.tv_controller.send_key("MEDIA_PAUSE"))
        btn_ff.clicked.connect(lambda: self.tv_controller.send_key("MEDIA_FAST_FORWARD"))
        btn_next.clicked.connect(lambda: self.tv_controller.send_key("MEDIA_NEXT"))
        
        row_media1.addWidget(btn_prev)
        row_media1.addWidget(btn_rew)
        row_media1.addWidget(btn_play)
        row_media1.addWidget(btn_pause)
        row_media1.addWidget(btn_ff)
        row_media1.addWidget(btn_next)
        
        row_media2 = QHBoxLayout()
        btn_stop = QPushButton("⏹ STOP")
        btn_stop.setFixedHeight(45)
        btn_stop.setFont(QFont("Inter", 11, QFont.Weight.DemiBold))
        btn_stop.clicked.connect(lambda: self.tv_controller.send_key("MEDIA_STOP"))
        row_media2.addWidget(btn_stop)
        
        media_layout.addLayout(row_media1)
        media_layout.addLayout(row_media2)
        remote_layout.addWidget(media_group)
        
        # Touchpad Setup
        touch_group = QGroupBox("Touchpad")
        touch_layout = QVBoxLayout(touch_group)
        self.touchpad = TouchpadWidget()
        self.touchpad.swipeSignal.connect(lambda d: self.tv_controller.send_key(d))
        self.touchpad.clickSignal.connect(lambda: self.tv_controller.send_key("DPAD_CENTER"))
        self.touchpad.backSignal.connect(lambda: self.tv_controller.send_key("BACK"))
        touch_layout.addWidget(self.touchpad)
        remote_layout.addWidget(touch_group)

        # Keyboard & Features (Consolidated)
        feat_group = QGroupBox("Keyboard Input")
        feat_layout = QVBoxLayout(feat_group)
        feat_layout.setContentsMargins(15, 20, 15, 15)
        
        self.chk_keyboard_grab = QCheckBox("Capture PC Keyboard (ESC, Arrows, etc.)")
        self.chk_keyboard_grab.setChecked(True)
        feat_layout.addWidget(self.chk_keyboard_grab)
        
        input_sub = QHBoxLayout()
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Type real-time to TV...")
        self.txt_input.textChanged.connect(self.on_realtime_text)
        self._last_text = "" # For tracking deltas
        self._ignore_sync = False # To prevent feedback loops
        
        # UI Polish: buttons removed as requested
        input_sub.addWidget(self.txt_input)
        feat_layout.addLayout(input_sub)

        # Screen Mirroring & Feature Removal
        # Moved redundant mirror checkbox to Settings
        
        remote_layout.addStretch()
        self.tabs.addTab(self.remote_scroll, "Remote")
        
        # -- SETTINGS TAB --
        self.settings_tab = QWidget()
        sets_layout = QVBoxLayout(self.settings_tab)
        sets_layout.setContentsMargins(20, 20, 20, 20)
        sets_layout.setSpacing(20)
        
        # Connection Status / Info
        info_group = QGroupBox("Active Connection")
        info_layout = QVBoxLayout(info_group)
        self.lbl_conn_info = QLabel("No device connected")
        self.lbl_conn_info.setStyleSheet("color: #8b949e;")
        info_layout.addWidget(self.lbl_conn_info)
        sets_layout.addWidget(info_group)
        
        # Mirroring & Advanced
        adv_group = QGroupBox("Advanced Features")
        adv_layout = QVBoxLayout(adv_group)
        
        self.chk_mirror_settings = QCheckBox("Enable Screen Mirroring (Requires ADB)")
        self.chk_mirror_settings.stateChanged.connect(self.toggle_mirroring)
        adv_layout.addWidget(self.chk_mirror_settings)
        
        btn_screenshot_settings = QPushButton("Capture TV Screenshot")
        btn_screenshot_settings.clicked.connect(self.take_screenshot_action)
        btn_screenshot_settings.setProperty("class", "accent")
        adv_layout.addWidget(btn_screenshot_settings)
        
        sets_layout.addWidget(adv_group)
        
        # Troubleshooting
        debug_group = QGroupBox("Troubleshooting")
        debug_layout = QVBoxLayout(debug_group)
        btn_reset_keys = QPushButton("Clear All Paired Devices")
        btn_reset_keys.setObjectName("btn_danger")
        btn_reset_keys.clicked.connect(self.reset_app_keys)
        debug_layout.addWidget(btn_reset_keys)
        debug_layout.addWidget(QLabel("<small><i>Resets certificates and forces new pairing.</i></small>"))
        sets_layout.addWidget(debug_group)
        
        sets_layout.addStretch()
        self.tabs.addTab(self.settings_tab, "Settings")

    def setup_callbacks(self):
        self.tv_controller.on_connect_callback = self.handle_connected
        self.tv_controller.on_disconnect_callback = self.handle_disconnected
        self.tv_controller.on_error_callback = self.handle_error
        self.tv_controller.on_text_updated_callback = self.handle_tv_text_update

    def handle_tv_text_update(self, text):
        """Update app input field when TV text changes."""
        if text == self.txt_input.text():
            return
            
        self._ignore_sync = True
        self.txt_input.setText(text)
        self._last_text = text
        self._ignore_sync = False
        self.update_status("Text synced from TV")

    # -- Device Discovery Logic --
    def on_device_found(self, device_info):
        self.device_found_sig.emit(device_info)

    def on_device_lost(self, device_info):
        self.device_lost_sig.emit(device_info)

    def _add_device_sub(self, device_info):
        ip = device_info['ip']
        port = device_info.get('port')
        
        # Determine status
        is_connected = self.tv_controller.is_connected and self.tv_controller.ip_address == ip
        is_paired = self.tv_controller.is_paired(ip)
        
        status_text = "Discovered"
        color = QColor("#888888") # Gray
        
        if is_connected:
            status_text = "Connected"
            color = QColor("#4CAF50") # Bright Green
        elif is_paired:
            status_text = "Paired"
            color = QColor("#FFC107") # Amber/Yellow
            
        display_text = f"{device_info['name']} ({ip}) - {status_text}"
        
        # Check if IP already exists by looking through all items
        existing_item = None
        for i in range(self.device_list_widget.count()):
            item = self.device_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == ip:
                existing_item = item
                break
        
        if not existing_item:
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, ip)
            item.setForeground(QBrush(color))
            self.device_list_widget.addItem(item)
            self.update_status(f"Found: {device_info['name']} ({status_text})")
            logger.info(f"Added device to UI: {display_text}")
        else:
            # Update existing item with better info/status if found
            if port == 6466 or is_connected or is_paired:
                existing_item.setText(display_text)
                existing_item.setForeground(QBrush(color))
                logger.info(f"Updated existing device info: {display_text}")

    def _remove_device_sub(self, device_info):
        display_text = f"({device_info['ip']})"
        items = self.device_list_widget.findItems(display_text, Qt.MatchFlag.MatchContains)
        for item in items:
            self.device_list_widget.takeItem(self.device_list_widget.row(item))

    def refresh_discovery(self):
        self.update_status("Refreshing discovery...")
        self.device_list_widget.clear()
        self.discovery.stop_discovery()
        self.discovery = DeviceDiscovery(self.on_device_found, self.on_device_lost)
        self.discovery.start_discovery()

    def on_device_lost(self, device_info):
        pass # Remove if needed

    # -- Connection Logic --
    @qasync.asyncSlot()
    async def connect_to_selected_device(self):
        item = self.device_list_widget.currentItem()
        if not item:
            return
            
        ip = item.data(Qt.ItemDataRole.UserRole)
        if not ip:
            return
            
        # Check if paired
        if not self.tv_controller.is_paired(ip):
            # Non-blocking dialog to avoid qasync re-entrancy on 3.14
            self.update_status(f"Device {ip} needs pairing...")
            asyncio.create_task(self._handle_unpaired_device(ip))
            return

        # Already paired, just connect in authorized mode
        await self._perform_connect(ip, wait_for_ready=True)

    async def _handle_unpaired_device(self, ip):
        """Handle device that needs pairing (non-blocking)."""
        reply = QMessageBox.question(self, 'Pair Device', 
                                    f'Device {ip} is not paired. Would you like to start pairing?',
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 1. Connect in pairing mode (don't wait for 'ready' signal)
            await self._perform_connect(ip, wait_for_ready=False)
            # 2. Start pairing flow
            await self.start_pairing_flow()

    def manual_connect_dialog(self):
        ip, ok = QInputDialog.getText(self, "Connect", "Enter TV IP Address:")
        if ok and ip:
            asyncio.create_task(self._perform_connect(ip))

    async def _perform_connect(self, ip, wait_for_ready=True):
        # Sanitize IP: extract just the IP if it's malformed (e.g. "1.2.3.4) - Model")
        import re
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ip)
        if ip_match:
            ip = ip_match.group(1)
        
        self.update_status(f"Attempting connection to {ip}...")
        try:
            await self.tv_controller.connect(ip, wait_for_ready=wait_for_ready)
        except Exception as e:
            self.show_error_message("Connection Error", str(e))
            self.update_status(f"Connection failed: {e}")

    def show_error_message(self, title, message):
        """Safely show error message from async context."""
        QTimer.singleShot(0, lambda: QMessageBox.critical(self, title, message))

    def show_info_message(self, title, message):
        """Safely show info message from async context."""
        QTimer.singleShot(0, lambda: QMessageBox.information(self, title, message))

    def show_warning_message(self, title, message):
        """Safely show warning message from async context."""
        QTimer.singleShot(0, lambda: QMessageBox.warning(self, title, message))

    def handle_connected(self):
        self.update_status("Connected!")
        self._refresh_device_list_ui()
        self.tabs.setCurrentIndex(1) # Switch to remote tab
        
        # If mirroring enabled, try to connect ADB
        if self.chk_mirror.isChecked():
            self.start_mirroring()

    def handle_disconnected(self):
        self.update_status("Disconnected")
        self._refresh_device_list_ui()

    def _refresh_device_list_ui(self):
        """Update existing list items with latest status colors."""
        for i in range(self.device_list_widget.count()):
            item = self.device_list_widget.item(i)
            ip = item.data(Qt.ItemDataRole.UserRole)
            if not ip: continue
            
            is_connected = self.tv_controller.is_connected and self.tv_controller.ip_address == ip
            is_paired = self.tv_controller.is_paired(ip)
            
            # Clean name (strip previous status)
            name = item.text().split(' (')[0]
            
            status_text = "Discovered"
            color = QColor("#888888")
            if is_connected:
                status_text = "Connected"
                color = QColor("#4CAF50")
            elif is_paired:
                status_text = "Paired"
                color = QColor("#FFC107")
                
            item.setText(f"{name} ({ip}) - {status_text}")
            item.setForeground(QBrush(color))

    def handle_error(self, msg):
        self.update_status(f"Error: {msg}")

    # -- Pairing Logic --
    @qasync.asyncSlot()
    async def reset_app_keys(self):
        reply = QMessageBox.question(self, 'Reset Pairs', 
                                    'Are you sure you want to delete all pairings? You will need to re-pair with all devices.',
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            success = await self.tv_controller.reset_keys()
            if success:
                QMessageBox.information(self, "Success", "Pairing keys reset. You can now try pairing again.")
            else:
                QMessageBox.critical(self, "Error", "Failed to reset pairing keys.")

    @qasync.asyncSlot()
    async def repair_selected_device(self):
        item = self.device_list_widget.currentItem()
        if not item:
            return
        ip = item.data(Qt.ItemDataRole.UserRole)
        # 1. Connect in pairing mode (must establish protocol session first)
        await self._perform_connect(ip, wait_for_ready=False)
        # 2. Start pairing flow
        await self.start_pairing_flow()

    @qasync.asyncSlot()
    async def start_pairing_flow(self):
        if not self.tv_controller.client:
            self.show_warning_message("Not Connected", "Please connect to a device first.")
            return
            
        try:
            self.update_status("Starting pairing on TV...")
            await self.tv_controller.start_pairing()
            
            # Prompt for code via dialog
            code, ok = QInputDialog.getText(self, "Pairing", "Enter the 6-character code shown on your TV:")
            if ok and code:
                self.txt_pairing_code.setText(code)
                await self.finish_pairing_flow()
        except Exception as e:
            self.show_error_message("Pairing Error", str(e))

    @qasync.asyncSlot()
    async def finish_pairing_flow(self):
        code = self.txt_pairing_code.text().strip()
        if not code:
            return
            
        try:
            self.update_status("Verifying pairing code...")
            await self.tv_controller.finish_pairing(code)
            self.update_status("Pairing successful! Re-connecting control channel...")
            self.txt_pairing_code.clear()
            
            # Immediately re-connect to establish functional control channel
            ip = self.tv_controller.ip_address
            if ip:
                await self._perform_connect(ip)
                # handle_connected will be called automatically on success
        except Exception as e:
            self.update_status(f"Pairing failed: {e}")
            self.show_error_message("Pairing Error", str(e))

    @qasync.asyncSlot()
    async def take_screenshot_action(self):
        if not self.adb_controller.connected_device_ip:
            # Try to connect ADB if not connected
            ip = self.tv_controller.ip_address
            if ip:
                self.update_status("Connecting ADB for screenshot...")
                success = self.adb_controller.connect(ip)
                if not success:
                    self.show_error_message("ADB Error", "Failed to connect to TV via ADB. Is ADB debugging enabled?")
                    return
            else:
                self.show_warning_message("Not Connected", "Please connect to a TV first.")
                return

        import datetime
        from pathlib import Path
        
        ss_dir = Path("screenshots")
        ss_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = ss_dir / f"screenshot_{timestamp}.png"
        
        self.update_status("Capturing screenshot...")
        success = self.adb_controller.take_screenshot(str(filename))
        
        if success:
            self.update_status(f"Screenshot saved: {filename.name}")
            # Optional: Open the folder or show the image
            QMessageBox.information(self, "Screenshot", f"Screenshot saved successfully to:\n{filename.absolute()}")
        else:
            self.show_error_message("Screenshot Error", "Failed to capture screenshot. Check if the screen is protected or ADB is busy.")

    # -- Mirroring --
    def toggle_mirroring(self, state):
        if not self.tv_controller.is_connected or not self.tv_controller.ip_address:
            # Revert check if not connected
            if state == Qt.CheckState.Checked.value:
                self.chk_mirror.setChecked(False)
                QMessageBox.warning(self, "Not Connected", "Connect to a TV first.")
            return

        if state == Qt.CheckState.Checked.value:
            self.start_mirroring()
        else:
            self.scrcpy_manager.stop_mirroring()

    def start_mirroring(self):
        ip = self.tv_controller.ip_address
        if not ip:
            return
            
        success = self.adb_controller.connect(ip)
        if success:
            self.scrcpy_manager.start_mirroring(ip)
        else:
            self.show_warning_message("ADB Error", "Failed to connect via ADB. Ensure ADB Debugging is enabled on TV.")
            self.chk_mirror.setChecked(False)

    # -- Keyboard --
    def on_realtime_text(self, text):
        if self._ignore_sync:
            return
            
        # Delta-based text sending
        if len(text) > len(self._last_text):
            # Characters added
            added = text[len(self._last_text):]
            self.tv_controller.send_text(added)
        elif len(text) < len(self._last_text):
            # Characters deleted
            diff_count = len(self._last_text) - len(text)
            for _ in range(diff_count):
                self.tv_controller.send_key("DEL")
        
        self._last_text = text

    def clear_realtime_input(self):
        self.txt_input.clear()
        self._last_text = ""

    def send_text_input(self):
        # Deprecated by real-time text, but kept for compatibility
        text = self.txt_input.text()
        if text:
            self.tv_controller.send_text(text)
            self.txt_input.clear()

    def update_status(self, msg):
        self.status_bar.showMessage(msg)

    # -- Keyboard Handling --
    def keyPressEvent(self, event: QKeyEvent):
        if not self.chk_keyboard_grab.isChecked():
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()
        
        # Map common keys to Android TV Remote key strings
        key_map = {
            Qt.Key.Key_Up: "DPAD_UP",
            Qt.Key.Key_Down: "DPAD_DOWN",
            Qt.Key.Key_Left: "DPAD_LEFT",
            Qt.Key.Key_Right: "DPAD_RIGHT",
            Qt.Key.Key_Return: "DPAD_CENTER",
            Qt.Key.Key_Enter: "DPAD_CENTER",
            Qt.Key.Key_Escape: "BACK",
            Qt.Key.Key_Backspace: "BACK",
            Qt.Key.Key_Home: "HOME",
            Qt.Key.Key_Menu: "SETTINGS",
            Qt.Key.Key_F1: "DPAD_UP",        # Alternative mappings
            Qt.Key.Key_F2: "DPAD_DOWN",
            Qt.Key.Key_F3: "DPAD_LEFT",
            Qt.Key.Key_F4: "DPAD_RIGHT",
            Qt.Key.Key_F5: "DPAD_CENTER",
            Qt.Key.Key_F12: "SETTINGS",
            Qt.Key.Key_PageUp: "VOLUME_UP",
            Qt.Key.Key_PageDown: "VOLUME_DOWN",
            Qt.Key.Key_Pause: "MEDIA_PLAY_PAUSE",
            Qt.Key.Key_MediaPlay: "MEDIA_PLAY_PAUSE",
            Qt.Key.Key_MediaStop: "MEDIA_STOP",
            Qt.Key.Key_MediaPrevious: "MEDIA_PREVIOUS",
            Qt.Key.Key_MediaNext: "MEDIA_NEXT",
        }

        # Alt+F4 for Power/Quit app (if imaginable)
        if key == Qt.Key.Key_F4 and modifiers & Qt.KeyboardModifier.AltModifier:
            self.tv_controller.send_key("POWER")
            return

        # Handle specific Character Keys if not a special mapping (and not capturing focusing LineEdit)
        if not self.txt_input.hasFocus():
            if key in key_map:
                self.tv_controller.send_key(key_map[key])
                return
            
            # Type individual characters directly if captured
            char = event.text()
            if char and char.isprintable():
                self.tv_controller.send_text(char)
                return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.discovery.stop_discovery()
        self.scrcpy_manager.stop_mirroring()
        asyncio.create_task(self.tv_controller.disconnect())
        event.accept()

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app = QApplication(sys.argv)
    
    # Modern Premium Dark Theme Stylesheet
    app.setStyleSheet("""
        QMainWindow, QWidget#devices_tab, QWidget#settings_tab {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
        }
        
        /* ScrollArea Styling */
        QScrollArea { border: none; background: transparent; }
        QScrollBar:vertical {
            border: none;
            background: #0d1117;
            width: 8px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #30363d;
            min-height: 20px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover { background: #484f58; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        
        QTabWidget::pane { 
            border: none;
            background: #0d1117;
            border-top: 1px solid #30363d;
        }
        
        QTabBar::tab {
            background: #161b22;
            color: #8b949e;
            padding: 10px 20px;
            border: 1px solid #30363d;
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 2px;
            min-width: 80px;
        }
        
        QTabBar::tab:selected {
            background: #0d1117;
            color: #58a6ff;
            border-bottom: 2px solid #58a6ff;
        }
        
        QGroupBox {
            background: rgba(22, 27, 34, 0.4);
            border: 1px solid #30363d;
            border-radius: 12px;
            margin-top: 20px;
            padding-top: 15px;
            font-weight: bold;
            color: #58a6ff;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
        }
        
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #21262d, stop:1 #161b22);
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 10px;
            color: #c9d1d9;
            font-weight: 500;
        }
        
        QPushButton:hover { background: #30363d; border-color: #8b949e; }
        QPushButton:pressed { background: #0d1117; }
        
        QPushButton[class="accent"] {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1f6feb, stop:1 #238636);
            color: white;
            border: none;
        }
        
        QPushButton#btn_center {
            border: 2px solid #58a6ff;
            background: rgba(88, 166, 255, 0.1);
        }
        
        QPushButton#btn_power {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #da3633, stop:1 #8e2a27);
            color: white;
            border: none;
        }
        
        QPushButton#btn_danger {
            background: rgba(248, 81, 73, 0.1);
            border: 1px solid #f85149;
            color: #f85149;
        }
        QPushButton#btn_danger:hover { background: #f85149; color: white; }
        
        QLineEdit {
            background: #010409;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 12px;
            color: #f0f0f0;
            font-size: 15px;
            selection-background-color: #58a6ff;
        }
        QLineEdit:focus { border-color: #58a6ff; }
        
        QListWidget {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 4px;
            outline: none;
        }
        QListWidget::item { padding: 10px; border-radius: 6px; }
        QListWidget::item:selected { background: #1f6feb; color: white; }
        
        QCheckBox { spacing: 8px; color: #8b949e; }
        QCheckBox::indicator { width: 18px; height: 18px; }
        
        QStatusBar { background: #010409; color: #8b949e; border-top: 1px solid #30363d; }
    """)
    
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = AndroidTVRemoteApp()
    window.show()
    
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()

