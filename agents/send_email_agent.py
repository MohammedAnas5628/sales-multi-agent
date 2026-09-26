from concurrent.futures import ThreadPoolExecutor, as_completed

from langgraph.types import interrupt

from core.state import SalesState
from tools.email_tools import send_email


# ============================================================
# SEND ONE EMAIL
# ============================================================

def _send_one_email(email_data: dict, sender_email: str):
    recipient = email_data.get("email")
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")

    if not recipient:
        return {
            **email_data,
            "status": "send_failed",
            "error": "No recipient email address.",
        }

    try:
        # Matches tools/email_tools.py exactly
        send_email(
            user_email=sender_email,
            to_email=recipient,
            subject=subject,
            body=body,
        )

        return {
            **email_data,
            "status": "sent",
        }

    except Exception as e:
        return {
            **email_data,
            "status": "send_failed",
            "error": str(e),
        }


# ============================================================
# BUILD APPROVAL PAYLOAD
# ============================================================

def _build_approval_payload(
    emails: list,
    sender_email: str,
):
    return {
        "type": "email_approval",
        "title": "EMAIL APPROVAL REQUIRED",
        "message": "Review the email draft before sending.",
        "sender_email": sender_email,
        "total_emails": len(emails),

        "emails": [
            {
                "index": index,
                "business_name": email.get(
                    "business_name",
                    "",
                ),
                "recipient": email.get(
                    "email",
                    "",
                ),
                "subject": email.get(
                    "subject",
                    "",
                ),
                "body": email.get(
                    "body",
                    "",
                ),
                "personalization_point": email.get(
                    "personalization_point",
                    "",
                ),
                "status": email.get(
                    "status",
                    "pending_approval",
                ),
            }
            for index, email in enumerate(
                emails,
                start=1,
            )
        ],

        "actions": [
            "approve",
            "edit",
            "reject",
        ],
    }


# ============================================================
# APPLY EDIT
# ============================================================

def _apply_edit(
    emails: list,
    decision: dict,
):
    updated_emails = [
        dict(email)
        for email in emails
    ]

    try:
        email_index = int(
            decision.get(
                "email_index",
                1,
            )
        ) - 1

    except (TypeError, ValueError):
        return updated_emails

    if (
        email_index < 0
        or email_index >= len(updated_emails)
    ):
        return updated_emails

    email = updated_emails[email_index]

    new_subject = decision.get("subject")
    new_body = decision.get("body")

    if new_subject is not None:
        new_subject = str(
            new_subject
        ).strip()

        if new_subject:
            email["subject"] = new_subject

    if new_body is not None:
        new_body = str(
            new_body
        ).strip()

        if new_body:
            email["body"] = new_body

    email["status"] = "pending_approval"

    updated_emails[email_index] = email

    return updated_emails


# ============================================================
# SEND EMAIL AGENT
# ============================================================

def send_email_agent(
    state: SalesState,
):
    emails = state.get(
        "emails",
        [],
    )

    sender_email = state.get(
        "user_email",
    )

    # --------------------------------------------------------
    # No emails
    # --------------------------------------------------------

    if not emails:
        return {
            **state,
            "approval_status": "no_emails",
            "status": "send_completed",
        }

    # --------------------------------------------------------
    # Missing sender
    # --------------------------------------------------------

    if not sender_email:
        return {
            **state,
            "approval_status": "failed",
            "status": "send_failed",
            "error": (
                "Authenticated sender email "
                "is missing."
            ),
        }

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    approval_payload = _build_approval_payload(
        emails=emails,
        sender_email=sender_email,
    )

    decision = interrupt(
        approval_payload
    )

    # --------------------------------------------------------
    # Normalize decision
    # --------------------------------------------------------

    if not isinstance(
        decision,
        dict,
    ):
        decision = {
            "action": str(
                decision
            ).strip().lower()
        }

    action = str(
        decision.get(
            "action",
            "",
        )
    ).strip().lower()

    # --------------------------------------------------------
    # EDIT
    #
    # The edited emails are saved back into state.
    # The graph/test router can send this node again
    # to show the updated draft for approval.
    # --------------------------------------------------------

    if action == "edit":

        updated_emails = _apply_edit(
            emails=emails,
            decision=decision,
        )

        return {
            **state,
            "emails": updated_emails,
            "approval_status": "pending",
            "status": "approval_pending",
        }

    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------

    if action == "reject":

        rejected_emails = []

        for email in emails:
            rejected_emails.append(
                {
                    **email,
                    "status": "rejected",
                }
            )

        return {
            **state,
            "emails": rejected_emails,
            "approval_status": "rejected",
            "status": "approval_rejected",
        }

    # --------------------------------------------------------
    # APPROVE
    # --------------------------------------------------------

    if action == "approve":

        print("\n" + "=" * 60)
        print("SENDING EMAILS")
        print("=" * 60)

        sent_emails = []

        with ThreadPoolExecutor(
            max_workers=3
        ) as executor:

            futures = [
                executor.submit(
                    _send_one_email,
                    email,
                    sender_email,
                )
                for email in emails
            ]

            for future in as_completed(
                futures
            ):
                try:
                    result = future.result()

                    sent_emails.append(
                        result
                    )

                except Exception as e:

                    sent_emails.append(
                        {
                            "status": "send_failed",
                            "error": str(e),
                        }
                    )

        sent_count = sum(
            1
            for email in sent_emails
            if email.get("status")
            == "sent"
        )

        failed_count = len(
            sent_emails
        ) - sent_count

        print(
            f"Sent   : {sent_count}"
        )

        print(
            f"Failed : {failed_count}"
        )

        # ----------------------------------------------------
        # Everything sent successfully
        # ----------------------------------------------------

        if failed_count == 0:

            return {
                **state,
                "emails": sent_emails,
                "approval_status": "approved",
                "status": "send_completed",
            }

        # ----------------------------------------------------
        # Some/all failed
        # ----------------------------------------------------

        return {
            **state,
            "emails": sent_emails,
            "approval_status": "approved",
            "status": "send_failed",
            "error": (
                f"{failed_count} email(s) failed to send."
            ),
        }

    # --------------------------------------------------------
    # INVALID ACTION
    # --------------------------------------------------------

    return {
        **state,
        "approval_status": "pending",
        "status": "approval_pending",
        "error": (
            "Invalid approval action."
        ),
    }