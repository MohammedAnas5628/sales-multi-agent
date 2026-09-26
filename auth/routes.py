from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import AuthorizedSession

from auth.google_oauth import (
    get_google_authorization_url,
    exchange_code_for_credentials,
)

from auth.token_manager import save_credentials


router = APIRouter(
    prefix="/auth/google",
    tags=["Google Authentication"],
)


@router.get("/login")
def google_login():
    """
    Start Google OAuth login.
    """

    (
        authorization_url,
        state,
        code_verifier,
    ) = get_google_authorization_url()

    response = RedirectResponse(
        url=authorization_url
    )

    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
    )

    response.set_cookie(
        key="oauth_code_verifier",
        value=code_verifier,
        httponly=True,
        samesite="lax",
    )

    return response


@router.get("/callback")
def google_callback(request: Request):
    """
    Handle Google's OAuth callback.
    """

    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        return {
            "error": "Authorization code not received"
        }

    if not state:
        return {
            "error": "OAuth state not received"
        }

    saved_state = request.cookies.get("oauth_state")
    code_verifier = request.cookies.get(
        "oauth_code_verifier"
    )

    if saved_state != state:
        return {
            "error": "Invalid OAuth state"
        }

    if not code_verifier:
        return {
            "error": "OAuth code verifier not found"
        }

    authorization_response = str(request.url)

    # Exchange authorization code for Google credentials
    credentials = exchange_code_for_credentials(
        authorization_response=authorization_response,
        state=state,
        code_verifier=code_verifier,
    )

    # Use Google's UserInfo endpoint to get the logged-in user's email
    session = AuthorizedSession(credentials)

    resp = session.get(
        "https://www.googleapis.com/oauth2/v2/userinfo"
    )

    resp.raise_for_status()

    profile = resp.json()

    user_email = profile.get("email")

    if not user_email:
        return {
            "error": "Could not determine Google account email"
        }

    print(f"Authenticated Google user: {user_email}")

    # Save encrypted credentials for this user
    save_credentials(
        user_email=user_email,
        credentials=credentials,
    )
    request.session["user_email"] = user_email

    # Redirect to success page
    response = RedirectResponse(
        url="/auth/google/success"
    )

    # Remove temporary OAuth cookies
    response.delete_cookie(
        key="oauth_state"
    )

    response.delete_cookie(
        key="oauth_code_verifier"
    )

    return response


@router.get("/success")
def google_success():
    """
    Successful Google authentication.
    """

    return {
        "message": "Google authentication successful",
        "status": "authenticated",
        "next_step": "Gmail sending is ready",
    }