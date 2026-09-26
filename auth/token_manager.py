import json
import os
from pathlib import Path

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
TOKEN_DIR = BASE_DIR / "data" / "google_tokens"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)

ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ValueError("TOKEN_ENCRYPTION_KEY not found in .env")

cipher = Fernet(ENCRYPTION_KEY.encode())


def _token_file(user_email: str) -> Path:
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    return TOKEN_DIR / f"{safe_email}.token"


def save_credentials(user_email: str, credentials: Credentials):
    """
    Encrypt and save Google OAuth credentials for a user.
    """

    token_data = credentials.to_json()

    encrypted_data = cipher.encrypt(
        token_data.encode()
    )

    file_path = _token_file(user_email)

    file_path.write_bytes(encrypted_data)

    print(f"Google credentials saved for {user_email}")


def load_credentials(user_email: str):
    """
    Load and decrypt Google OAuth credentials for a user.
    """

    file_path = _token_file(user_email)

    if not file_path.exists():
        return None

    encrypted_data = file_path.read_bytes()

    decrypted_data = cipher.decrypt(
        encrypted_data
    ).decode()

    credentials_info = json.loads(decrypted_data)

    return Credentials.from_authorized_user_info(
        credentials_info
    )


def delete_credentials(user_email: str):
    """
    Delete stored Google credentials for a user.
    """

    file_path = _token_file(user_email)

    if file_path.exists():
        file_path.unlink()
        print(f"Google credentials deleted for {user_email}")