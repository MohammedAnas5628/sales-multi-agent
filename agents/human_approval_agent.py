from langgraph.types import interrupt

from core.state import SalesState


def human_approval_agent(state: SalesState) -> SalesState:
    """
    Human review step.

    Actions:
    - approve -> send emails
    - edit    -> update one email and review again
    - reject  -> stop without sending
    """

    emails = state.get("emails", [])

    if not emails:
        return {
            **state,
            "approval_status": "rejected",
            "status": "approval_rejected",
        }

    approval_payload = {
        "message": "Review the generated emails before sending.",
        "total_emails": len(emails),
        "sender_email": state.get("user_email"),
        "emails": [
            {
                "index": index,
                "business_name": email.get("business_name"),
                "recipient": email.get("email"),
                "subject": email.get("subject"),
                "body": email.get("body"),
                "status": email.get("status"),
            }
            for index, email in enumerate(emails)
        ],
        "actions": [
            "approve",
            "edit",
            "reject",
        ],
    }

    # Pause workflow
    decision = interrupt(approval_payload)

    if not isinstance(decision, dict):
        return {
            **state,
            "approval_status": "rejected",
            "status": "approval_rejected",
        }

    action = decision.get("action")

    # ========================================================
    # APPROVE
    # ========================================================

    if action == "approve":

        print("\nHuman Approval: APPROVED")

        return {
            **state,
            "approval_status": "approved",
            "status": "approval_approved",
        }

    # ========================================================
    # REJECT
    # ========================================================

    if action == "reject":

        print("\nHuman Approval: REJECTED")

        return {
            **state,
            "approval_status": "rejected",
            "status": "approval_rejected",
        }

    # ========================================================
    # EDIT
    # ========================================================

    if action == "edit":

        email_index = decision.get("email_index")
        new_subject = decision.get("subject")
        new_body = decision.get("body")

        if email_index is None:
            raise ValueError(
                "email_index is required when editing an email."
            )

        if not isinstance(email_index, int):
            raise ValueError(
                "email_index must be an integer."
            )

        if email_index < 0 or email_index >= len(emails):
            raise ValueError(
                "Invalid email_index."
            )

        if not new_subject or not new_body:
            raise ValueError(
                "Edited email must contain subject and body."
            )

        updated_emails = list(emails)

        updated_emails[email_index] = {
            **updated_emails[email_index],
            "subject": new_subject.strip(),
            "body": new_body.strip(),
            "status": "pending_approval",
        }

        print(
            f"\nEmail edited for "
            f"{updated_emails[email_index].get('business_name')}"
        )

        # Go back to approval screen
        return {
            **state,
            "emails": updated_emails,
            "approval_status": "pending",
            "status": "email_pending_approval",
        }

    # ========================================================
    # INVALID ACTION
    # ========================================================

    return {
        **state,
        "approval_status": "rejected",
        "status": "approval_invalid_action",
    }