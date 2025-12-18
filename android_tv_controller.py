import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable
from androidtvremote2 import AndroidTVRemote
from config import cfg

logger = logging.getLogger(__name__)

class CustomAndroidTVRemote(AndroidTVRemote):
    """
    Subclass of AndroidTVRemote to capture text updates from the TV.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_text_updated_callback: Optional[Callable[[str], None]] = None

    def _handle_message(self, raw_msg: bytes) -> None:
        """Override to intercept IME messages."""
        from androidtvremote2.remotemessage_pb2 import RemoteMessage
        msg = RemoteMessage()
        try:
            msg.ParseFromString(raw_msg)
        except Exception:
            pass # Library handles parsing errors too
        
        if msg.HasField("remote_ime_batch_edit"):
            # Extract text from the batch edit
            for edit_info in msg.remote_ime_batch_edit.edit_info:
                if edit_info.HasField("text_field_status"):
                    text = edit_info.text_field_status.value
                    logger.info(f"TV text update received: {text}")
                    if self.on_text_updated_callback:
                        self.on_text_updated_callback(text)
        
        # Call original handler to process other messages
        super()._handle_message(raw_msg)

class AndroidTVController:
    """
    Manages connection and control of an Android TV using the Android TV Remote Protocol v2.
    """
    
    def __init__(self):
        self.client: Optional[CustomAndroidTVRemote] = None
        self.ip_address: Optional[str] = None
        self.on_connect_callback: Optional[Callable] = None
        self.on_disconnect_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        self.on_text_updated_callback: Optional[Callable[[str], None]] = None
        self.is_connected = False
        self.connection_lock = asyncio.Lock()
        
        # Paths for keys
        self.cert_path = str(cfg.KEYS_DIR / "cert.pem")
        self.key_path = str(cfg.KEYS_DIR / "key.pem")

    async def connect(self, ip_address: str, wait_for_ready: bool = True) -> bool:
        """Connect to Android TV at the given IP."""
        if self.client and self.is_connected and self.ip_address == ip_address:
            return True

        async with self.connection_lock:
            self.ip_address = ip_address
            
            # Diagnostic check
            logger.info(f"Running network diagnostics for {ip_address}...")
            is_reachable = await self._check_port(ip_address, 6466)
            if not is_reachable:
                error_msg = f"Port 6466 is closed on {ip_address}. Is the TV on and on the same network?"
                logger.error(error_msg)
                if self.on_error_callback:
                    self.on_error_callback(error_msg)
                return False
                
            logger.info(f"Port 6466 is open. Connecting to {ip_address}...")
            
            # Try to connect with retries
            for attempt in range(1, 3):
                try:
                    # Re-initialize client
                    if self.client:
                        logger.info("Disconnecting previous client before retry...")
                        await self._disconnect_internal()

                    logger.info(f"Connection attempt {attempt} to {ip_address}...")
                    self.client = CustomAndroidTVRemote(
                        client_name="Linux TV Remote",
                        certfile=self.cert_path,
                        keyfile=self.key_path,
                        host=ip_address
                    )
                    self.client.on_text_updated_callback = self.on_text_updated_callback
                    
                    await self.client.async_generate_cert_if_missing()
                    
                    ready_event = asyncio.Event()
                    def availability_callback(is_available):
                        logger.info(f"Availability signal: {is_available}")
                        self.is_connected = is_available
                        if is_available:
                            ready_event.set()
                            if self.on_connect_callback:
                                self.on_connect_callback()
                        else:
                            if self.on_disconnect_callback:
                                self.on_disconnect_callback()

                    self.client.add_is_available_updated_callback(availability_callback)
                    
                    await self.client.async_connect()
                    
                    # Optimistic connection: the transport is up!
                    self.is_connected = True
                    if self.on_connect_callback:
                        self.on_connect_callback()
                    
                    if not wait_for_ready:
                        logger.info("Connection transport established (pairing/fast mode).")
                        return True
                        
                    # Handshake check (non-blocking for the return)
                    try:
                        logger.info(f"Waiting for TV handshake (attempt {attempt})...")
                        # Some TVs are very slow to send 'available', we'll wait a bit 
                        # but we won't block the caller if they want to send keys immediately.
                        await asyncio.wait_for(ready_event.wait(), timeout=5.0)
                        logger.info("TV handshake complete.")
                    except asyncio.TimeoutError:
                        logger.warning(f"Handshake slow on attempt {attempt}. Proceeding optimistically.")
                    
                    self.client.keep_reconnecting()
                    cfg.set("last_connected_device_ip", ip_address)
                    return True
                            
                except Exception as e:
                    logger.error(f"Connect failed on attempt {attempt}: {e}")
                    self.is_connected = False
                    if attempt == 1:
                        await asyncio.sleep(1)
                        continue
                    if self.on_error_callback:
                        self.on_error_callback(str(e))
                    return False
            
            return False


    async def disconnect(self):
        """Disconnect from the current device."""
        async with self.connection_lock:
            await self._disconnect_internal()

    async def _disconnect_internal(self):
        """Internal disconnect logic (no lock)."""
        if self.client:
            logger.info("Disconnecting client...")
            self.client.disconnect() 
            self.client = None
            self.is_connected = False

    async def start_pairing(self):
        """Start pairing process."""
        if not self.client:
            return
        await self.client.async_start_pairing()

    async def finish_pairing(self, code: str):
        """Submit pairing code."""
        if not self.client:
            return
        await self.client.async_finish_pairing(code)
        
        # Mark as paired in config
        if self.ip_address:
            self.mark_paired(self.ip_address)

    def is_paired(self, ip_address: str) -> bool:
        """Check if a device is known to be paired."""
        paired_list = cfg.get("paired_devices", [])
        return ip_address in paired_list

    def mark_paired(self, ip_address: str):
        """Mark a device as paired in config."""
        paired_list = cfg.get("paired_devices", [])
        if ip_address not in paired_list:
            paired_list.append(ip_address)
            cfg.set("paired_devices", paired_list)

    def send_key(self, key_code: str, direction: str = "SHORT"):
        """
        Send a key press. 
        """
        if not self.client:
            logger.warning(f"send_key: No client initialized. Key: {key_code}")
            return
        
        # Logging state
        logger.info(f"send_key attempt: {key_code}, is_connected={self.is_connected}")
        
        try:
            self.client.send_key_command(key_code, direction)
        except Exception as e:
            logger.error(f"Failed to send key: {e}")

    def send_text(self, text: str):
        """Send text input (keyboard forwarding)."""
        if not self.client or not self.is_connected:
            return
        
        try:
            # Try bulk send text first
            logger.info(f"Sending bulk text: {text}")
            self.client.send_text(text)
        except Exception as e:
            logger.warning(f"Bulk send_text failed, using character fallback: {e}")
            # Fallback: send text character by character might be needed for some apps
            # but usually the library handles this. 
            # If we really need fallback, we'd need a map of char -> keycode.
            pass

    async def launch_app(self, app_link: str):
        """Launch an app on Android TV."""
        if not self.client or not self.is_connected:
            return
        try:
            self.client.send_launch_app_command(app_link)
        except Exception as e:
            logger.error(f"Failed to launch app: {e}")
        
    async def reset_keys(self):
        """Delete current keys to force a fresh pairing."""
        await self.disconnect()
        try:
            cert = Path(self.cert_path)
            key = Path(self.key_path)
            if cert.exists(): cert.unlink()
            if key.exists(): key.unlink()
            
            # Also clear paired devices list
            cfg.set("paired_devices", [])
            
            logger.info("Keys successfully reset.")
            return True
        except Exception as e:
            logger.error(f"Failed to reset keys: {e}")
            return False

    async def _check_port(self, host: str, port: int, timeout: float = 3.0) -> bool:
        """Check if a TCP port is open."""
        try:
            conn = asyncio.open_connection(host, port)
            await asyncio.wait_for(conn, timeout=timeout)
            return True
        except:
            return False

    def stop_voice(self):
        pass


