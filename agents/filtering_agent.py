from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field

from core.llm import llm
from core.state import SalesState


class LeadQualification(BaseModel):
    qualified: bool = Field(
        description="True only if this business is a usable, contactable, real sales lead matching the request"
    )
    confidence: float = Field(
        description="0.0 to 1.0 — how confident you are in this decision given the available data"
    )
    reason: str = Field(
        description="One short sentence explaining the decision, referencing the specific signal that drove it"
    )


structured_llm = llm.with_structured_output(LeadQualification)


SYSTEM_PROMPT = """You are a B2B sales lead qualification agent. You evaluate one business at a time \
against a target business type and location, and decide if it is worth a sales outreach attempt.

QUALIFY the lead if ALL of these hold:
1. Category/name reasonably matches the requested business type (don't be overly strict on wording — \
"Dental clinic" matches a request for "dentists").
2. City reasonably matches the requested location.
3. At least one contact method exists: phone, email, or website.
4. The business shows signs of being active/real — e.g. has a Google rating and a non-trivial review \
count, OR has a working website. A listing with zero reviews AND no website AND no rating is a weak signal.

DO NOT reject a lead just because email is missing — phone or website alone is enough.
DO NOT reject a lead for having a low rating — rating quality is not a qualification criterion, only \
whether the business appears to be real and operating.

Be decisive. If data is genuinely too thin to judge, qualify=false with confidence < 0.5 and say why."""


def _build_user_message(lead: dict, business_type: str, location: str) -> str:
    return f"""Requested business type: {business_type}
Requested location: {location}

Business information:
Name: {lead.get("title")}
Category: {lead.get("categoryName")}
City: {lead.get("city")}
Website: {lead.get("website")}
Phone: {lead.get("phone")}
Email: {lead.get("emails")}
Google Rating: {lead.get("totalScore")}
Reviews: {lead.get("reviewsCount")}"""


def _qualify_one(lead: dict, business_type: str, location: str):
    messages = [
        ("system", SYSTEM_PROMPT),
        ("human", _build_user_message(lead, business_type, location)),
    ]

    try:
        result = structured_llm.invoke(messages)
    except Exception as e:
        print(f"Qualification failed for {lead.get('title')}: {e}")
        return lead, None

    return lead, result


def filtering_agent(state: SalesState) -> SalesState:

    leads = state.get("leads", [])
    business_type = state.get("business_type", "")
    location = state.get("location", "")

    qualified_leads = []

    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = [
            executor.submit(_qualify_one, lead, business_type, location)
            for lead in leads
        ]

        for future in as_completed(futures):

            lead, result = future.result()

            if result is None:
                # LLM/API error — don't silently drop, don't silently accept either
                print(f"Skipping (error): {lead.get('title')}")
                continue

            print("\n--- Filtering Agent ---")
            print("Business:", lead.get("title"))
            print("Qualified:", result.qualified)
            print("Confidence:", result.confidence)
            print("Reason:", result.reason)

            if result.qualified:
                qualified_leads.append({
                    **lead,
                    "qualification_reason": result.reason,
                    "qualification_confidence": result.confidence,
                })

    return {
        **state,
        "qualified_leads": qualified_leads,
        "status": "filtering_completed",
    }