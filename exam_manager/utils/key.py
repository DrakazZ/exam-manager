import os
import string
from cryptography.fernet import Fernet

def find_key_on_any_drive():
    for drive_letter in string.ascii_uppercase:
        drive_path = f"{drive_letter}:/"
        key_path = os.path.join(drive_path, "secret.key")
        if os.path.exists(key_path):
            return key_path
    return None

def load_key():
    usb_key_path = find_key_on_any_drive()
    local_key_path = os.path.join(os.getcwd(), "secret.key")

    if usb_key_path and os.path.exists(usb_key_path):
        with open(usb_key_path, "rb") as f:
            return f.read(), f"✅ Key loaded from USB: {usb_key_path}"

    if os.path.exists(local_key_path):
        with open(local_key_path, "rb") as f:
            return f.read(), "✅ Local key loaded."

    # Generate new key
    key = Fernet.generate_key()
    with open(local_key_path, "wb") as f:
        f.write(key)
    return key, "🔐 New local key generated."