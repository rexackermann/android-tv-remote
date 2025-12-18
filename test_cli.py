import asyncio
import logging
import sys
from androidtvremote2 import AndroidTVRemote

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_remote(ip_address):
    cert_path = "cert_test.pem"
    key_path = "key_test.pem"
    
    remote = AndroidTVRemote(
        client_name="Test Remote CLI",
        certfile=cert_path,
        keyfile=key_path,
        host=ip_address
    )
    
    await remote.async_generate_cert_if_missing()
    
    def on_available(is_available):
        print(f"\n[STATUS] Device available: {is_available}")

    remote.add_is_available_updated_callback(on_available)
    
    print(f"Connecting to {ip_address}...")
    try:
        await remote.async_connect()
    except Exception as e:
        print(f"Connect failed: {e}. Starting pairing...")
        await remote.async_start_pairing()
        code = input("Enter pairing code from TV: ")
        await remote.async_finish_pairing(code)
        print("Pairing finished. Reconnecting...")
        await remote.async_connect()

    print("\nConnected! Testing keys in 2 seconds...")
    await asyncio.sleep(2)
    
    test_keys = ["HOME", "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT", "BACK"]
    
    for key in test_keys:
        print(f"Sending key: {key}")
        remote.send_key_command(key, "SHORT")
        await asyncio.sleep(1)
        
    print("\nTest complete. Disconnecting...")
    remote.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_cli.py <TV_IP>")
        sys.exit(1)
    
    asyncio.run(test_remote(sys.argv[1]))
