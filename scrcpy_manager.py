# Copyright (c) 2025 Rex Ackermann. All rights reserved.
# Licensed under the MIT License.
import subprocess
import logging
from typing import Optional
from config import cfg

logger = logging.getLogger(__name__)

class ScrcpyManager:
    """
    Manages the scrcpy process for screen mirroring.
    """
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.scrcpy_path = cfg.get("scrcpy_path", "scrcpy")

    def start_mirroring(self, ip_address: str, embed_window_id: Optional[int] = None):
        """
        Start scrcpy for the given IP.
        embed_window_id: X11 window ID to embed into (for Qt integration)
        """
        if self.process and self.process.poll() is None:
            logger.warning("Scrcpy already running")
            return

        cmd = [
            self.scrcpy_path,
            "--serial", f"{ip_address}:5555",  # Target specific device
            "--window-title", f"Mirror: {ip_address}",
            "--stay-awake",
            # Optimization for wireless
            "--max-size", str(cfg.get("screen_mirroring").get("max_size", 1024)),
            "--video-bit-rate", str(cfg.get("screen_mirroring").get("bitrate", 4000000)),
            "--max-fps", str(cfg.get("screen_mirroring").get("max_fps", 30))
        ]

        if not cfg.get("audio_forwarding", True):
            cmd.append("--no-audio")

        # Embedding implementation implies passing correct window ID
        # SDL_WINDOWID environment variable is often used by scrcpy (SDL based)
        env = None
        if embed_window_id:
             import os
             env = os.environ.copy()
             env["SDL_WINDOWID"] = str(embed_window_id)

        try:
            logger.info(f"Starting scrcpy: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            logger.error("Scrcpy executable not found")
        except Exception as e:
            logger.error(f"Failed to start scrcpy: {e}")

    def stop_mirroring(self):
        """Stop the scrcpy process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

