import re

from core.apify_token_manager import (
    apify_manager,
)


# ============================================================
# ACTOR
# ============================================================

ACTOR_ID = (
    "compass/crawler-google-places"
)


# ============================================================
# EMAIL CLEANING
# ============================================================

def _clean_email(
    email: str | None,
) -> str | None:

    if not email:
        return None

    email = (
        email
        .strip()
        .lower()
        .strip(
            " <>[](){}\"',;"
        )
    )

    pattern = (
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    if not re.match(
        pattern,
        email,
    ):

        return None

    return email


# ============================================================
# EMAIL EXTRACTION
# ============================================================

def _extract_emails(
    values,
) -> list[str]:

    if not values:
        return []

    if isinstance(
        values,
        str,
    ):

        values = [
            values
        ]

    emails = []

    for value in values:

        if not isinstance(
            value,
            str,
        ):

            continue

        email = _clean_email(
            value
        )

        if (
            email
            and email not in emails
        ):

            emails.append(
                email
            )

    return emails


# ============================================================
# GOOGLE MAPS SEARCH
# ============================================================

def search_google_maps(
    query: str,
    max_results: int = 5,
) -> list[dict]:

    """
    Search Google Maps using Apify.

    max_results:
        Maximum number of businesses to return.
        Hard-capped to 1-50.
    """

    # --------------------------------------------------------
    # Validate max_results
    # --------------------------------------------------------

    try:

        max_results = int(
            max_results
        )

    except (
        TypeError,
        ValueError,
    ):

        max_results = 5

    max_results = max(
        1,
        min(
            50,
            max_results,
        ),
    )

    print("\n" + "=" * 60)
    print("GOOGLE MAPS TOOL")
    print("=" * 60)

    print(
        "Query:",
        query,
    )

    print(
        "Maximum Results:",
        max_results,
    )

    # --------------------------------------------------------
    # Apify input
    # --------------------------------------------------------

    run_input = {

        "searchStringsArray": [
            query
        ],

        "maxCrawledPlaces":
            max_results,

        "includeReviews":
            False,

        "scrapeContacts":
            True,
    }

    # --------------------------------------------------------
    # RUN ACTOR WITH TOKEN FAILOVER
    # --------------------------------------------------------

    client, run = (
        apify_manager.run_actor(
            ACTOR_ID,
            run_input,
        )
    )

    # --------------------------------------------------------
    # READ DATASET
    # --------------------------------------------------------

    dataset_items = (
        client
        .dataset(
            run.default_dataset_id
        )
        .iterate_items()
    )

    leads = []

    # --------------------------------------------------------
    # PROCESS RESULTS
    # --------------------------------------------------------

    for item in dataset_items:

        if len(leads) >= max_results:

            break

        business_name = (
            item.get("title")
            or item.get("name")
        )

        if not business_name:

            continue

        category = (
            item.get("categoryName")
            or item.get("category")
        )

        city = (
            item.get("city")
            or item.get("locality")
        )

        website = item.get(
            "website"
        )

        phone = item.get(
            "phone"
        )

        rating = item.get(
            "totalScore"
        )

        reviews_count = item.get(
            "reviewsCount"
        )

        maps_url = item.get(
            "url"
        )

        emails = _extract_emails(
            item.get(
                "emails"
            )
        )

        # ----------------------------------------------------
        # Existing email enrichment logic
        # ----------------------------------------------------

        if (
            not emails
            and website
        ):

            try:

                from tools.email_finder import (
                    find_business_email,
                )

                found_email = (
                    find_business_email(
                        website
                    )
                )

                found_email = _clean_email(
                    found_email
                )

                if found_email:

                    emails.append(
                        found_email
                    )

            except Exception as error:

                print(
                    f"[Email Finder] Website lookup "
                    f"failed for {business_name}: "
                    f"{error}"
                )

        if not emails:

            try:

                from tools.email_finder import (
                    find_email_via_search,
                )

                found_email = (
                    find_email_via_search(
                        business_name,
                        city,
                    )
                )

                found_email = _clean_email(
                    found_email
                )

                if found_email:

                    emails.append(
                        found_email
                    )

            except Exception as error:

                print(
                    f"[Email Finder] Search lookup "
                    f"failed for {business_name}: "
                    f"{error}"
                )

        # ----------------------------------------------------
        # Normalized lead
        # ----------------------------------------------------

        lead = {

            "title":
                business_name,

            "categoryName":
                category,

            "city":
                city,

            "website":
                website,

            "phone":
                phone,

            "emails":
                emails,

            "totalScore":
                rating,

            "reviewsCount":
                reviews_count,

            "url":
                maps_url,
        }

        leads.append(
            lead
        )

    # --------------------------------------------------------
    # Hard cap
    # --------------------------------------------------------

    leads = leads[
        :max_results
    ]

    print(
        "\nFinal leads returned:",
        len(leads),
    )

    return leads


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    results = search_google_maps(
        query=(
            "coworking spaces "
            "in Hyderabad"
        ),
        max_results=3,
    )

    print(
        "\nReturned:",
        len(results),
    )

    for index, lead in enumerate(
        results,
        start=1,
    ):

        print(
            f"{index}. "
            f"{lead.get('title')}"
        )

        print(
            "   Phone:",
            lead.get("phone"),
        )

        print(
            "   Email:",
            lead.get("emails"),
        )