import os

from dotenv import load_dotenv
from apify_client import ApifyClient


load_dotenv()

APIFY_API_TOKEN = os.getenv(
    "APIFY_API_TOKEN"
)

JOBS_ACTOR_ID = os.getenv(
    "APIFY_JOBS_ACTOR_ID"
)

if not APIFY_API_TOKEN:
    raise ValueError(
        "APIFY_API_TOKEN not found in .env"
    )

client = ApifyClient(
    APIFY_API_TOKEN
)


# =========================================================
# JOB SEARCH
# =========================================================

def search_jobs(
    query: str,
    max_results: int = 20,
) -> list[dict]:

    if not query:
        return []

    if not JOBS_ACTOR_ID:

        print(
            "APIFY_JOBS_ACTOR_ID "
            "not configured."
        )

        return []

    try:

        run = client.actor(
            JOBS_ACTOR_ID
        ).call(
            run_input={
                "jobSearches": [
                    query
                ],
            }
        )

        dataset_id = (
            run.default_dataset_id
        )

        jobs = (
            client.dataset(
                dataset_id
            )
            .list_items()
            .items
        )

        return jobs[:max_results]

    except Exception as e:

        print(
            f"[jobs_tools] "
            f"Job search failed: {e}"
        )

        return []


# =========================================================
# COMPANY JOBS
# =========================================================

def search_company_jobs(
    company_name: str,
    location: str | None = None,
    max_results: int = 20,
) -> list[dict]:

    query = company_name

    if location:
        query += f" {location}"

    return search_jobs(
        query=query,
        max_results=max_results,
    )


# =========================================================
# HIRING SIGNAL
# =========================================================

def build_hiring_evidence(
    jobs: list[dict],
) -> dict:

    titles = []

    for job in jobs:

        title = (
            job.get("title")
            or job.get("jobTitle")
        )

        if title:
            titles.append(title)

    return {
        "job_count": len(jobs),
        "job_titles": titles,
        "evidence": jobs,
    }