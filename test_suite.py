import unittest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from android_tv_controller import AndroidTVController

class TestTVRemote(unittest.TestCase):
    
    def test_config_defaults(self):
        """Test configuration default values."""
        cfg = Config()
        self.assertEqual(cfg.get("app_name", "Android TV Remote"), "Android TV Remote")
        self.assertTrue(cfg.get("audio_forwarding"))
        
    def test_config_persistence(self):
        """Test saving and loading config."""
        cfg = Config()
        original_theme = cfg.get("theme")
        
        # Change value
        cfg.set("theme", "light")
        self.assertEqual(cfg.get("theme"), "light")
        
        # Reload (simulate app restart)
        new_cfg = Config()
        self.assertEqual(new_cfg.get("theme"), "light")
        
        # Restore
        cfg.set("theme", original_theme)

    def test_controller_initialization(self):
        """Test logic for controller setup."""
        controller = AndroidTVController()
        self.assertFalse(controller.is_connected)
        self.assertIsNone(controller.ip_address)
        
        # Check if keys are generated
        config = controller.get_config()
        self.assertTrue(os.path.exists(config.client_cert_path))
        self.assertTrue(os.path.exists(config.client_key_path))

if __name__ == '__main__':
    unittest.main()
