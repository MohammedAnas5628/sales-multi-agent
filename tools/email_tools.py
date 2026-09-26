import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from auth.token_manager import load_credentials, save_credentials


def send_email(
    user_email: str,
    to_email: str,
    subject: str,
    body: str,
):
    """
    Send an email from the authenticated user's Gmail account.
    """

    print("\n" + "=" * 60)
    print("GMAIL SEND")
    print("=" * 60)

    print(f"From    : {user_email}")
    print(f"To      : {to_email}")
    print(f"Subject : {subject}")

    # --------------------------------------------------------
    # Load OAuth credentials
    # --------------------------------------------------------

    credentials = load_credentials(user_email)

    if not credentials:
        raise ValueError(
            f"No Google credentials found for {user_email}. "
            "Please login with Google first."
        )

    # --------------------------------------------------------
    # Refresh expired token
    # --------------------------------------------------------

    if credentials.expired and credentials.refresh_token:

        print("Access token expired. Refreshing...")

        credentials.refresh(Request())

        save_credentials(
            user_email=user_email,
            credentials=credentials,
        )

        print("Google credentials refreshed.")

    # --------------------------------------------------------
    # Gmail API service
    # --------------------------------------------------------

    gmail_service = build(
        "gmail",
        "v1",
        credentials=credentials,
    )

    # --------------------------------------------------------
    # Build email
    # --------------------------------------------------------

    message = MIMEText(
        body,
        "plain",
        "utf-8",
    )

    message["To"] = to_email
    message["Subject"] = subject

    # --------------------------------------------------------
    # Encode
    # --------------------------------------------------------

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    # --------------------------------------------------------
    # Send
    # --------------------------------------------------------

    sent = (
        gmail_service.users()
        .messages()
        .send(
            userId="me",
            body={
                "raw": raw_message
            },
        )
        .execute()
    )

    message_id = sent.get("id")
    thread_id = sent.get("threadId")

    print("\nEmail sent successfully.")
    print(f"Message ID: {message_id}")
    print(f"Thread ID : {thread_id}")

    return sent