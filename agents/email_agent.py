import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from core.llm import llm
from core.state import SalesState


# ============================================================
# ENV
# ============================================================

load_dotenv()

SENDER_NAME = os.getenv(
    "SENDER_NAME",
    "Sales Team"
)

COMPANY_NAME = os.getenv(
    "COMPANY_NAME",
    "Our Company"
)


# ============================================================
# EMAIL OUTPUT
# ============================================================

class GeneratedEmail(BaseModel):

    subject: str = Field(
        description="Short professional subject. Maximum 8 words."
    )

    body: str = Field(
        description=(
            "Short personalized sales email body. "
            "40-70 words. Mention office chairs and end with "
            "one simple CTA question. No greeting or sign-off."
        )
    )

    personalization_point: str = Field(
        description=(
            "One short factual research point used to personalize "
            "the email."
        )
    )


email_llm = llm.with_structured_output(
    GeneratedEmail,
    method="json_mode"
)


# ============================================================
# PROMPT
# ============================================================

SYSTEM_PROMPT = f"""
You are a B2B sales email writer.

We sell office chairs to businesses.

Write short, natural and personalized cold emails.

Rules:

- Product = office chairs.
- Use only facts provided in the lead and research.
- Never invent facts.
- Use ONE research fact for personalization.
- Explain briefly why office chairs may be relevant.
- End with ONE simple CTA question.
- 40-70 words.
- No greeting.
- No sign-off.
- Do not use placeholders.
- Keep it human and direct.

Return ONLY valid JSON with:

{{
  "subject": "...",
  "body": "...",
  "personalization_point": "..."
}}
"""


# ============================================================
# BUILD CONTEXT
# ============================================================

def _build_lead_context(
    lead: dict
) -> str:

    research = lead.get(
        "research",
        {}
    )

    return f"""
BUSINESS
Name: {lead.get("title")}
Category: {lead.get("categoryName")}
City: {lead.get("city")}
Website: {lead.get("website")}
Email: {lead.get("emails")}
Phone: {lead.get("phone")}

WEB RESEARCH

Company Information:
{research.get("company_information", [])}

Recent Activity:
{research.get("recent_activity", [])}

Website Information:
{research.get("website", [])}
"""


# ============================================================
# GENERATE EMAIL
# ============================================================

def _generate_email(
    lead: dict
):

    email_list = lead.get(
        "emails",
        []
    )

    if not email_list:

        print(
            f"[Email] No email found for "
            f"{lead.get('title')}"
        )

        return lead, None

    context = _build_lead_context(
        lead
    )

    prompt = f"""
Create a short personalized sales email for this business.

{context}

Write the email using ONE useful fact from the web research.

Product:
office chairs
"""

    try:

        result = email_llm.invoke(
            [
                (
                    "system",
                    SYSTEM_PROMPT
                ),
                (
                    "human",
                    prompt
                )
            ]
        )

        body = result.body.strip()

        # Basic safety validation
        if (
            "office chair" not in body.lower()
            or "?" not in body
            or len(body.split()) < 25
            or len(body.split()) > 90
        ):

            print(
                f"[Email] Invalid draft for "
                f"{lead.get('title')}"
            )

            return lead, None

        return lead, result

    except Exception as e:

        print(
            f"[Email] Failed for "
            f"{lead.get('title')}: {e}"
        )

        return lead, None


# ============================================================
# EMAIL AGENT
# ============================================================

def email_agent(
    state: SalesState
) -> SalesState:

    leads = state.get(
        "researched_leads",
        []
    )

    emails = []

    print(
        "\n"
        + "=" * 60
    )

    print(
        "EMAIL AGENT"
    )

    print(
        "=" * 60
    )

    if not leads:

        print(
            "No researched leads available."
        )

        return {
            **state,
            "emails": [],
            "status": "email_completed",
        }

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        futures = [
            executor.submit(
                _generate_email,
                lead
            )
            for lead in leads
        ]

        for future in as_completed(
            futures
        ):

            lead, result = (
                future.result()
            )

            if result is None:

                print(
                    f"[Email] Skipped: "
                    f"{lead.get('title')}"
                )

                continue

            email_address = (
                lead.get("emails", [None])[0]
            )

            business_name = (
                lead.get("title")
                or "team"
            )

            full_body = (
                f"Hi {business_name} team,\n\n"
                f"{result.body.strip()}\n\n"
                f"Best,\n"
                f"{SENDER_NAME}\n"
                f"{COMPANY_NAME}"
            )

            email_data = {

                "business_name":
                    business_name,

                "email":
                    email_address,

                "phone":
                    lead.get("phone"),

                "website":
                    lead.get("website"),

                "subject":
                    result.subject.strip(),

                "body":
                    full_body,

                "personalization_point":
                    result.personalization_point.strip(),

                "sales_potential":
                    lead.get(
                        "sales_potential",
                        {}
                    ),

                "status":
                    "pending_approval",
            }

            emails.append(
                email_data
            )

            print(
                "\n--- Email Draft ---"
            )

            print(
                "Business:",
                business_name
            )

            print(
                "To:",
                email_address
            )

            print(
                "Subject:",
                email_data["subject"]
            )

            print(
                "\n"
                + email_data["body"]
            )

            print(
                "\nStatus: Pending Approval"
            )

    print(
        f"\nEmails generated: "
        f"{len(emails)}"
    )

    return {
        **state,
        "emails": emails,
        "status": "email_completed",
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    test_state: SalesState = {

        "researched_leads": [

            {
                "title":
                    "Example Coworking Space",

                "categoryName":
                    "Coworking Space",

                "city":
                    "Hyderabad",

                "website":
                    "https://example.com",

                "emails":
                    ["contact@example.com"],

                "phone":
                    "+91XXXXXXXXXX",

                "research": {

                    "company_information": [
                        {
                            "title":
                                "Example Coworking Space",

                            "content":
                                "Coworking facility with workstations and meeting areas."
                        }
                    ],

                    "recent_activity": [
                        {
                            "title":
                                "Business activity",

                            "content":
                                "The business maintains an active web presence."
                        }
                    ],

                    "website": []
                }
            }
        ]
    }

    result = email_agent(
        test_state
    )

    print(
        "\nGenerated:",
        len(
            result.get(
                "emails",
                []
            )
        )
    )