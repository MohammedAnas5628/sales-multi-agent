from core.state import SalesState
from tools.maps_tools import search_google_maps
from tools.email_finder import (
    find_business_email,
    find_email_via_search,
)


# ============================================================
# MAPS AGENT
# ============================================================

def maps_agent(
    state: SalesState,
) -> SalesState:

    print("\n" + "=" * 60)
    print("MAPS AGENT")
    print("=" * 60)

    # --------------------------------------------------------
    # Read search information from state
    # --------------------------------------------------------

    search_query = state.get(
        "search_query",
        "",
    )

    location = state.get(
        "location",
        "",
    )

    # --------------------------------------------------------
    # Read requested lead limit
    # --------------------------------------------------------

    lead_limit = state.get(
        "lead_limit",
        5,
    )

    # Safety validation
    try:

        lead_limit = int(
            lead_limit
        )

    except (
        TypeError,
        ValueError,
    ):

        lead_limit = 5

    # Hard limit: 1-50
    lead_limit = max(
        1,
        min(
            50,
            lead_limit,
        ),
    )

    # --------------------------------------------------------
    # Build Maps query
    # --------------------------------------------------------

    if location:

        query = (
            f"{search_query} "
            f"in {location}"
        )

    else:

        query = search_query

    print(
        "Search Query:",
        query,
    )

    print(
        "Requested Lead Limit:",
        lead_limit,
    )

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not search_query:

        print(
            "Maps Agent failed: "
            "search query is missing."
        )

        return {

            **state,

            "leads": [],

            "status":
                "maps_failed",

            "error":
                "Search query is missing.",
        }

    # --------------------------------------------------------
    # Search Google Maps through Apify
    # --------------------------------------------------------

    try:

        leads = search_google_maps(
            query=query,
            max_results=lead_limit,
        )

    except Exception as e:

        print(
            "Maps search failed:",
            e,
        )

        return {

            **state,

            "leads": [],

            "status":
                "maps_failed",

            "error":
                str(e),
        }

    # --------------------------------------------------------
    # HARD SAFETY CAP
    # --------------------------------------------------------

    if not leads:

        print(
            "No leads found."
        )

        return {

            **state,

            "leads": [],

            "status":
                "maps_completed",
        }

    leads = leads[
        :lead_limit
    ]

    # ========================================================
    # EMAIL FINDER ENRICHMENT
    # ========================================================

    print(
        "\n" + "-" * 60
    )

    print(
        "EMAIL FINDER"
    )

    print(
        "-" * 60
    )

    for index, lead in enumerate(
        leads,
        start=1,
    ):

        business_name = (
            lead.get("title")
            or ""
        )

        city = (
            lead.get("city")
            or location
            or ""
        )

        # ----------------------------------------------------
        # Check whether Maps already provided an email
        # ----------------------------------------------------

        existing_emails = (
            lead.get("emails")
            or []
        )

        existing_email = (
            lead.get("email")
            or (
                existing_emails[0]
                if existing_emails
                else None
            )
        )

        if existing_email:

            # Normalize email fields so downstream
            # agents can use either format.
            lead["email"] = existing_email
            lead["emails"] = [
                existing_email
            ]

            print(
                f"\n{index}. "
                f"{business_name}"
            )

            print(
                "   Email already available:",
                existing_email,
            )

            continue

        print(
            f"\n{index}. "
            f"{business_name}"
        )

        print(
            "   No email from Maps."
        )

        # ----------------------------------------------------
        # Step 1: Try website contact extraction
        # ----------------------------------------------------

        website = (
            lead.get("website")
            or ""
        )

        found_email = None

        if website:

            print(
                "   Trying website email finder..."
            )

            found_email = (
                find_business_email(
                    website
                )
            )

        # ----------------------------------------------------
        # Step 2: Google Search fallback
        # ----------------------------------------------------

        if not found_email:

            print(
                "   Website email not found."
            )

            print(
                "   Trying Google Search fallback..."
            )

            if business_name:

                found_email = (
                    find_email_via_search(
                        business_name,
                        city,
                    )
                )

        # ----------------------------------------------------
        # Attach found email to lead
        # ----------------------------------------------------

        if found_email:

            lead["email"] = (
                found_email
            )

            lead["emails"] = [
                found_email
            ]

            print(
                "   Email found:",
                found_email,
            )

        else:

            print(
                "   No usable email found."
            )

    # --------------------------------------------------------
    # Display enriched results
    # --------------------------------------------------------

    print(
        "\n" + "-" * 60
    )

    print(
        "ENRICHED LEADS"
    )

    print(
        "-" * 60
    )

    print(
        "\nLeads Found:",
        len(leads),
    )

    print(
        "Maximum Allowed:",
        lead_limit,
    )

    for index, lead in enumerate(
        leads,
        start=1,
    ):

        print(
            f"\n{index}. "
            f"{lead.get('title')}"
        )

        print(
            "   Category:",
            lead.get(
                "categoryName"
            ),
        )

        print(
            "   City:",
            lead.get(
                "city"
            ),
        )

        print(
            "   Phone:",
            lead.get(
                "phone"
            ),
        )

        print(
            "   Email:",
            (
                lead.get("emails")
                or []
            ),
        )

    # --------------------------------------------------------
    # Return updated state
    # --------------------------------------------------------

    return {

        **state,

        "leads":
            leads,

        "status":
            "maps_completed",

        "current_stage":
            "filtering",
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    test_state: SalesState = {

        "user_request":
            "Dental clinics in Hyderabad",

        "search_query":
            "Dental clinics",

        "location":
            "Hyderabad",

        "lead_limit":
            3,
    }

    result = maps_agent(
        test_state
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "MAPS TEST COMPLETED"
    )

    print(
        "=" * 60
    )

    print(
        "Requested:",
        test_state[
            "lead_limit"
        ],
    )

    print(
        "Returned:",
        len(
            result.get(
                "leads",
                [],
            )
        ),
    )