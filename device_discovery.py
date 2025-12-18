from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
import threading
# Copyright (c) 2025 Rex Ackermann. All rights reserved.
# Licensed under the MIT License.
import socket
import logging
from typing import Callable, Dict

logger = logging.getLogger(__name__)

class DeviceDiscovery:
    """
    Discovers Android TV devices on the local network using mDNS (Zeroconf).
    Looking for _androidtvremote2._tcp.local. service.
    """
    
    def __init__(self, on_device_found: Callable, on_device_lost: Callable):
        self.zeroconf = Zeroconf()
        self.browser = None
        self.on_device_found = on_device_found
        self.on_device_lost = on_device_lost
        self.discovered_devices: Dict[str, dict] = {} # ip -> info

    def start_discovery(self):
        """Start scanning for devices."""
        logger.info("Starting device discovery...")
        # The service types for Android TV Remote Protocol
        # v2 is the standard for modern apps
        service_v2 = "_androidtvremote2._tcp.local."
        # v1 might still be active on some older devices
        service_v1 = "_androidtvremote._tcp.local."
        # googlecast can help identify the device even if remote protocol is blocked
        service_cast = "_googlecast._tcp.local."
        
        self.browser = ServiceBrowser(
            self.zeroconf, 
            [service_v2, service_v1, service_cast], 
            handlers=[self._on_service_state_change]
        )

    def stop_discovery(self):
        """Stop scanning."""
        if self.browser:
            self.browser.cancel()
            self.browser = None
        self.zeroconf.close()

    def _on_service_state_change(self, zeroconf, service_type, name, state_change):
        """Callback for Zeroconf service changes."""
        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                self._process_service_info(info)
        
        elif state_change is ServiceStateChange.Removed:
            # name is like "Living Room TV._androidtvremote2._tcp.local."
            # We assume unique names map to devices we track
            pass

    def _process_service_info(self, info):
        """Extract details from service info."""
        addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
        if not addresses:
            return
            
        ip = addresses[0]
        port = info.port
        server_name = info.server
        
        # Decode properties if available (often contains model info)
        properties = {}
        for key, value in info.properties.items():
            try:
                properties[key.decode('utf-8')] = value.decode('utf-8') if value else ""
            except:
                pass

        device_name = properties.get("n", server_name.split('.')[0])
        
        device_info = {
            "name": device_name,
            "ip": ip,
            "port": port,
            "model": properties.get("m", "Unknown Model"),
            "manufacturer": properties.get("mf", "Unknown")
        }
        
        logger.info(f"Discovered device: {device_info}")
        self.discovered_devices[ip] = device_info
        self.on_device_found(device_info)

