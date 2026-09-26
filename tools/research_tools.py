import os
import re
from urllib.parse import urlparse

from dotenv import load_dotenv
from apify_client import ApifyClient


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not APIFY_API_TOKEN:
    raise ValueError("APIFY_API_TOKEN not found in .env")

client = ApifyClient(APIFY_API_TOKEN)

GOOGLE_SEARCH_ACTOR = "apify/google-search-scraper"

EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _run_google_search(
    query: str,
    results_per_page: int = 10,
    max_pages: int = 1,
) -> list[dict]:

    if not query:
        return []

    try:

        run = client.actor(
            GOOGLE_SEARCH_ACTOR
        ).call(
            run_input={
                "queries": query,
                "resultsPerPage": results_per_page,
                "maxPagesPerQuery": max_pages,
            }
        )

        dataset_id = run.default_dataset_id

        rows = client.dataset(
            dataset_id
        ).list_items().items

        if not rows:
            return []

        organic_results = []

        for row in rows:

            organic = row.get(
                "organicResults",
                []
            )

            organic_results.extend(
                organic
            )

        return organic_results

    except Exception as e:

        print(
            f"[research_tools] Google search failed: {e}"
        )

        return []


def _unique_results(
    results: list[dict],
) -> list[dict]:

    seen = set()
    unique = []

    for item in results:

        url = item.get("url")

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)
        unique.append(item)

    return unique


# =========================================================
# GENERAL WEB SEARCH
# =========================================================

def search_web(
    query: str,
    max_results: int = 10,
) -> list[dict]:

    results = _run_google_search(
        query=query,
        results_per_page=min(max_results, 100),
        max_pages=1,
    )

    return _unique_results(
        results
    )[:max_results]


# =========================================================
# COMPANY SEARCH
# =========================================================

def search_company(
    business_name: str,
    city: str | None = None,
) -> list[dict]:

    query = f'"{business_name}"'

    if city:
        query += f' "{city}"'

    query += (
        " company services contact"
    )

    return search_web(
        query,
        max_results=10,
    )


# =========================================================
# NEWS / RECENT DEVELOPMENTS
# =========================================================

def search_business_news(
    business_name: str,
    city: str | None = None,
) -> list[dict]:

    query = f'"{business_name}"'

    if city:
        query += f' "{city}"'

    query += (
        " news OR expansion OR "
        "relocation OR opening OR "
        "new branch OR growth"
    )

    return search_web(
        query,
        max_results=10,
    )


# =========================================================
# HIRING / BUSINESS ACTIVITY
# =========================================================

def search_business_activity(
    business_name: str,
    city: str | None = None,
) -> list[dict]:

    query = f'"{business_name}"'

    if city:
        query += f' "{city}"'

    query += (
        " hiring OR jobs OR careers "
        "OR recruitment"
    )

    return search_web(
        query,
        max_results=10,
    )


# =========================================================
# WEBSITE RESEARCH
# =========================================================

def research_website(
    website: str,
) -> dict:

    if not website:
        return {
            "website": None,
            "domain": None,
            "pages": [],
            "emails": [],
        }

    website = website.rstrip("/")

    parsed = urlparse(
        website
    )

    domain = parsed.netloc

    if not domain:
        return {
            "website": website,
            "domain": None,
            "pages": [],
            "emails": [],
        }

    queries = [
        f"site:{domain} about",
        f"site:{domain} services",
        f"site:{domain} contact",
        f"site:{domain} team",
    ]

    pages = []
    emails = []

    for query in queries:

        results = search_web(
            query,
            max_results=5,
        )

        for result in results:

            page = {
                "title": result.get(
                    "title"
                ),
                "url": result.get(
                    "url"
                ),
                "description": result.get(
                    "description"
                ),
            }

            pages.append(page)

            text = " ".join([
                page["title"] or "",
                page["description"] or "",
            ])

            emails.extend(
                EMAIL_REGEX.findall(
                    text
                )
            )

    return {
        "website": website,
        "domain": domain,
        "pages": _unique_results(pages),
        "emails": list(
            dict.fromkeys(emails)
        ),
    }


# =========================================================
# COMPLETE COMPANY RESEARCH
# =========================================================

def research_company(
    business_name: str,
    city: str | None = None,
    website: str | None = None,
) -> dict:

    result = {
        "business_name": business_name,
        "city": city,
        "company_information": [],
        "news": [],
        "activity": [],
        "website": {},
    }

    result["company_information"] = (
        search_company(
            business_name,
            city,
        )
    )

    result["news"] = (
        search_business_news(
            business_name,
            city,
        )
    )

    result["activity"] = (
        search_business_activity(
            business_name,
            city,
        )
    )

    if website:

        result["website"] = (
            research_website(
                website
            )
        )

    return result


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    data = research_company(
        business_name=(
            "V Care N Cure "
            "Multi-speciality "
            "Dental Clinic"
        ),
        city="Hyderabad",
        website=(
            "http://www.vcarencure.com/"
        ),
    )

    print("\nCOMPANY INFORMATION")
    print(data["company_information"])

    print("\nNEWS")
    print(data["news"])

    print("\nACTIVITY")
    print(data["activity"])

    print("\nWEBSITE")
    print(data["website"])