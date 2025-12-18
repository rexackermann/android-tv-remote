import logging
import subprocess
from typing import Optional, List
from config import cfg

logger = logging.getLogger(__name__)

class ADBController:
    """
    Optional ADB controller for advanced features like Screen Mirroring,
    App Installation, and File Transfer.
    """
    
    def __init__(self):
        self.adb_path = cfg.get("adb_path", "adb")
        self.connected_device_ip: Optional[str] = None
    
    def _run_command(self, cmd_args: List[str]) -> tuple[bool, str]:
        """Run an ADB command."""
        try:
            full_cmd = [self.adb_path] + cmd_args
            result = subprocess.run(
                full_cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0, result.stdout.strip()
        except FileNotFoundError:
            logger.error("ADB binary not found")
            return False, "ADB binary not found"
        except Exception as e:
            logger.error(f"ADB command failed: {e}")
            return False, str(e)

    def connect(self, ip_address: str) -> bool:
        """Connect to device via ADB TCP/IP."""
        # 5555 is default TCPIP port
        logger.info(f"ADB connecting to {ip_address}...")
        success, output = self._run_command(["connect", f"{ip_address}:5555"])
        
        # Output usually: "connected to x.x.x.x:5555" or "already connected"
        if success and ("connected" in output):
            self.connected_device_ip = ip_address
            return True
        return False

    def is_available(self) -> bool:
        """Check if ADB tool is available."""
        success, _ = self._run_command(["version"])
        return success

    def install_apk(self, apk_path: str) -> bool:
        """Install an APK file."""
        if not self.connected_device_ip:
            return False
        
        success, output = self._run_command([
            "-s", f"{self.connected_device_ip}:5555", 
            "install", "-r", apk_path
        ])
        return success

    def push_file(self, local_path: str, remote_path: str) -> bool:
        """Push file to device."""
        if not self.connected_device_ip:
            return False
            
        success, output = self._run_command([
            "-s", f"{self.connected_device_ip}:5555",
            "push", local_path, remote_path
        ])
        return success

    def take_screenshot(self, local_path: str) -> bool:
        """Take screenshot and pull to local path."""
        if not self.connected_device_ip:
            return False
            
        remote_path = "/sdcard/screenshot.png"
        
        # 1. Take screencap
        success, _ = self._run_command([
            "-s", f"{self.connected_device_ip}:5555",
            "shell", "screencap", "-p", remote_path
        ])
        if not success:
            return False
            
        # 2. Pull file
        success, _ = self._run_command([
            "-s", f"{self.connected_device_ip}:5555",
            "pull", remote_path, local_path
        ])
        
        # 3. Cleanup remote file
        self._run_command([
            "-s", f"{self.connected_device_ip}:5555",
            "shell", "rm", remote_path
        ])
        
        return success

