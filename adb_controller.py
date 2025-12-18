import logging
# Copyright (c) 2025 Rex Ackermann. All rights reserved.
# Licensed under the MIT License.
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
        self._shell_process: Optional[subprocess.Popen] = None
    
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
        logger.info(f"ADB connecting to {ip_address}...")
        success, output = self._run_command(["connect", f"{ip_address}:5555"])
        
        if success and ("connected" in output or "already" in output):
            self.connected_device_ip = ip_address
            # Pre-start persistent shell for fast input
            self._ensure_shell()
            return True
        return False

    def _ensure_shell(self):
        """Ensure a persistent shell is running for fast input."""
        if not self.connected_device_ip:
            return
            
        if self._shell_process and self._shell_process.poll() is None:
            return # Already running
            
        try:
            logger.info("Starting persistent ADB shell process...")
            cmd = [self.adb_path, "-s", f"{self.connected_device_ip}:5555", "shell"]
            self._shell_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1 # Line buffered
            )
        except Exception as e:
            logger.error(f"Failed to start persistent shell: {e}")

    def close(self):
        """Closes the persistent shell process."""
        if self._shell_process:
            try:
                self._shell_process.stdin.write("exit\n")
                self._shell_process.stdin.flush()
                self._shell_process.terminate()
                self._shell_process.wait(timeout=1)
            except:
                pass
            self._shell_process = None

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

    def send_text(self, text: str) -> bool:
        """Send text using high-speed persistent shell."""
        if not self.connected_device_ip:
            return False
        
        self._ensure_shell()
        if not self._shell_process:
            return False
            
        try:
            # Persistent shell is much faster as it avoids spawning process per letter
            escaped_text = text.replace(" ", "%s").replace("'", "\\'")
            self._shell_process.stdin.write(f"input text '{escaped_text}'\n")
            self._shell_process.stdin.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to send text via persistent shell: {e}")
            self._shell_process = None # Force restart on next call
            return False

    def send_key(self, keycode: int) -> bool:
        """Send keyevent using high-speed persistent shell."""
        if not self.connected_device_ip:
            return False
            
        self._ensure_shell()
        if not self._shell_process:
            return False
            
        try:
            self._shell_process.stdin.write(f"input keyevent {keycode}\n")
            self._shell_process.stdin.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to send key via persistent shell: {e}")
            self._shell_process = None
            return False

