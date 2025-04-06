import os
import hashlib
from cryptography.fernet import Fernet

CLIENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../client"))
KEY_FILE = os.path.join(CLIENT_DIR, "encryption_key.key")

def load_key():
    """Carga la clave de cifrado o la genera si no existe."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    with open(KEY_FILE, "rb") as f:
        return f.read()

KEY = load_key()
cipher = Fernet(KEY)

def encrypt_chunk(data):
    """Cifra un fragmento de datos."""
    return cipher.encrypt(data)

def decrypt_chunk(data):
    """Descifra un fragmento de datos."""
    try:
        return cipher.decrypt(data)
    except Exception:
        print("[✖] Error al descifrar un fragmento. Puede estar corrupto.")
        return None
