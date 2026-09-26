from concurrent.futures import ThreadPoolExecutor, as_completed

from core.state import SalesState
from tools.tavily_tools import (
    search_company,
    search_recent_activity,
    search_website,
)


def research_one(lead: dict):
    business_name = lead.get("title", "")
    city = lead.get("city", "")
    website = lead.get("website")

    print(f"[Tavily] Researching: {business_name}")

    company_information = []
    recent_activity = []
    website_information = []

    try:
        company_information = search_company(
            business_name,
            city,
        )
    except Exception as e:
        print(f"[Tavily] Company search failed: {e}")

    try:
        recent_activity = search_recent_activity(
            business_name,
            city,
        )
    except Exception as e:
        print(f"[Tavily] Activity search failed: {e}")

    if website:
        try:
            website_information = search_website(
                website
            )
        except Exception as e:
            print(f"[Tavily] Website search failed: {e}")

    return {
        **lead,
        "research": {
            "company_information": company_information,
            "recent_activity": recent_activity,
            "website": website_information,

            # Kept for compatibility with Excel/export code
            "hiring_signals": [],
            "expansion_signals": [],
            "funding_signals": [],
            "workplace_signals": [],
        },
        "sales_potential": {
            "useful_for_product": True,
            "relevance": "MEDIUM",
            "reason": "Basic web research collected for email personalization.",
            "key_reasons": [],
            "sales_opportunity": (
                "Potential office-chair sales opportunity "
                "based on business context."
            ),
            "recommended_action": "CONSIDER",
        },
        "research_depth": "BASIC",
        "research_depth_reason": (
            "Simple web research for email personalization."
        ),
    }


def deduplicate_leads(leads):
    seen = set()
    unique_leads = []

    for lead in leads:
        name = lead.get("title", "").strip().lower()
        phone = lead.get("phone", "")
        email = lead.get("email", "")

        key = (name, phone, email)

        if key not in seen:
            seen.add(key)
            unique_leads.append(lead)

    return unique_leads


def research_agent(state: SalesState):
    qualified_leads = state.get("qualified_leads", [])

    if not qualified_leads:
        print("[Research] No qualified leads.")
        return {
            **state,
            "researched_leads": [],
            "status": "research_completed",
        }

    qualified_leads = deduplicate_leads(qualified_leads)

    print("\n" + "=" * 60)
    print("RESEARCH AGENT")
    print("=" * 60)
    print(f"Researching {len(qualified_leads)} lead(s)...")

    researched_leads = []

    with ThreadPoolExecutor(max_workers=3) as executor:

        futures = [
            executor.submit(research_one, lead)
            for lead in qualified_leads
        ]

        for future in as_completed(futures):
            try:
                result = future.result()

                if result:
                    researched_leads.append(result)

            except Exception as e:
                print(f"[Research] Lead research failed: {e}")

    print(f"Research completed: {len(researched_leads)} lead(s)")

    return {
        **state,
        "researched_leads": researched_leads,
        "status": "research_completed",
    }