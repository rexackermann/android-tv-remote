# Copyright (c) 2025 Rex Ackermann. All rights reserved.
# Licensed under the MIT License.
import os
import json
from pathlib import Path

class Config:
    APP_NAME = "Android TV Remote"
    VERSION = "1.0.0"
    
    # Default paths
    CONFIG_DIR = Path.home() / ".config" / "android-tv-remote"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    KEYS_DIR = CONFIG_DIR / "keys"  # For caching SSL certificates/keys
    
    # Default settings
    DEFAULT_CONFIG = {
        "last_connected_device_ip": None,
        "paired_devices": [], # List of IPs that have been paired
        "theme": "dark",
        "screen_mirroring": {
            "enabled": False,
            "max_size": 1024,
            "bitrate": 8000000,
            "max_fps": 30,
            "stay_awake": True
        },
        "audio_forwarding": True,
        "input": {
            "mouse_sensitivity": 1.0,
            "scroll_sensitivity": 1.0,
            "tap_to_click": True
        },
        "adb_path": "adb",  # Assumes 'adb' is in PATH by default
        "scrcpy_path": "scrcpy"  # Assumes 'scrcpy' is in PATH by default
    }

    def __init__(self):
        self._ensure_config_dir()
        self.settings = self._load_config()

    def _ensure_config_dir(self):
        """Ensure configuration directories exist."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.KEYS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """Load configuration from file or create with defaults."""
        if not self.CONFIG_FILE.exists():
            return self.save_config(self.DEFAULT_CONFIG)
        
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                config = self.DEFAULT_CONFIG.copy()
                self._recursive_update(config, saved_config)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG

    def _recursive_update(self, d, u):
        """Recursively update dictionary d with values from u."""
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._recursive_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def save_config(self, settings=None):
        """Save current settings to file."""
        if settings:
            self.settings = settings
        
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return self.settings
        except Exception as e:
            print(f"Error saving config: {e}")
            return self.settings

    def get(self, key, default=None):
        """Get a configuration value."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Set a configuration value and save."""
        self.settings[key] = value
        self.save_config()

# Global config instance
cfg = Config()
