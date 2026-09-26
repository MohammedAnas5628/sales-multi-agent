import os

from dotenv import load_dotenv
from apify_client import ApifyClient


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

APIFY_API_TOKEN = os.getenv(
    "APIFY_API_TOKEN"
)

LINKEDIN_ACTOR_ID = os.getenv(
    "APIFY_LINKEDIN_ACTOR_ID"
)

if not APIFY_API_TOKEN:
    raise ValueError(
        "APIFY_API_TOKEN not found in .env"
    )

client = ApifyClient(
    APIFY_API_TOKEN
)


# =========================================================
# INTERNAL ACTOR RUNNER
# =========================================================

def _run_linkedin_actor(
    run_input: dict,
) -> list[dict]:

    if not LINKEDIN_ACTOR_ID:

        print(
            "APIFY_LINKEDIN_ACTOR_ID "
            "not configured."
        )

        return []

    try:

        run = client.actor(
            LINKEDIN_ACTOR_ID
        ).call(
            run_input=run_input
        )

        dataset_id = (
            run.default_dataset_id
        )

        return (
            client.dataset(
                dataset_id
            )
            .list_items()
            .items
        )

    except Exception as e:

        print(
            f"[linkedin_tools] "
            f"Actor failed: {e}"
        )

        return []


# =========================================================
# COMPANY
# =========================================================

def search_linkedin_company(
    company_url: str,
) -> list[dict]:

    if not company_url:
        return []

    return _run_linkedin_actor({

        "companyUrls": [
            company_url
        ]

    })


# =========================================================
# PEOPLE
# =========================================================

def search_linkedin_people(
    profile_urls: list[str],
) -> list[dict]:

    if not profile_urls:
        return []

    return _run_linkedin_actor({

        "profileUrls": profile_urls

    })


# =========================================================
# COMPANY + PEOPLE
# =========================================================

def research_linkedin(
    company_url: str | None = None,
    profile_urls: list[str] | None = None,
) -> dict:

    result = {
        "company": [],
        "people": [],
    }

    if company_url:

        result["company"] = (
            search_linkedin_company(
                company_url
            )
        )

    if profile_urls:

        result["people"] = (
            search_linkedin_people(
                profile_urls
            )
        )

    return result