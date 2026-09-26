import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from requests.exceptions import SSLError, ConnectionError as RequestsConnectionError


# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
load_dotenv(BASE_DIR / ".env")


# Local development only.
# DO NOT use this in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

REDIRECT_URI = "http://localhost:8000/auth/google/callback"


SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.send",
]


if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID not found in .env")

if not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_SECRET not found in .env")


def create_google_flow(
    state: str | None = None,
    code_verifier: str | None = None,
):
    """
    Create Google OAuth flow.
    """

    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier,
    )

    flow.redirect_uri = REDIRECT_URI

    return flow


def get_google_authorization_url():
    """
    Generate Google authorization URL.

    Returns:
        authorization_url
        state
        code_verifier
    """

    flow = create_google_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return (
        authorization_url,
        state,
        flow.code_verifier,
    )


def exchange_code_for_credentials(
    authorization_response: str,
    state: str,
    code_verifier: str,
    max_retries: int = 3,
):
    """
    Exchange Google's authorization code for OAuth credentials.

    Retries on transient SSL/connection errors — Windows + some
    ISP/AV setups occasionally drop the TLS handshake to Google's
    token endpoint for no code-related reason. A fresh attempt
    almost always succeeds within 1-2 retries.
    """

    flow = create_google_flow(
        state=state,
        code_verifier=code_verifier,
    )

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            flow.fetch_token(
                authorization_response=authorization_response
            )
            return flow.credentials

        except (SSLError, RequestsConnectionError) as e:
            last_error = e
            print(
                f"Transient network error on token exchange "
                f"(attempt {attempt}/{max_retries}): {e}"
            )

            if attempt < max_retries:
                time.sleep(1.5 * attempt)

    raise last_error