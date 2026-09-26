import os

from dotenv import load_dotenv
from tavily import TavilyClient


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY not found in .env"
    )

client = TavilyClient(
    api_key=TAVILY_API_KEY
)


# =========================================================
# SEARCH
# =========================================================

def search_web(
    query: str,
    max_results: int = 3,
) -> list[dict]:

    if not query:
        return []

    try:

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
            topic="general",
        )

        results = []

        for item in response.get(
            "results",
            []
        ):

            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get(
                    "content",
                    ""
                )[:1000],
                "published_date": item.get(
                    "published_date"
                ),
            })

        return results

    except Exception as e:

        print(
            f"[Tavily] Search failed: {e}"
        )

        return []


# =========================================================
# COMPANY INFORMATION
# =========================================================

def search_company(
    business_name: str,
    city: str,
) -> list[dict]:

    query = (
        f'"{business_name}" '
        f'"{city}" '
        "company services industry"
    )

    return search_web(
        query,
        max_results=3,
    )


# =========================================================
# RECENT BUSINESS ACTIVITY
# =========================================================

def search_recent_activity(
    business_name: str,
    city: str,
) -> list[dict]:

    query = (
        f'"{business_name}" '
        f'"{city}" '
        "("
        "news OR announcement OR "
        "milestone OR growth OR "
        "partnership"
        ")"
    )

    return search_web(
        query,
        max_results=3,
    )


# =========================================================
# HIRING
# =========================================================

def search_hiring(
    business_name: str,
    city: str,
) -> list[dict]:

    query = (
        f'"{business_name}" '
        f'"{city}" '
        "("
        "hiring OR recruitment OR "
        "jobs OR careers OR "
        "vacancies"
        ")"
    )

    return search_web(
        query,
        max_results=3,
    )


# =========================================================
# EXPANSION
# =========================================================

def search_expansion(
    business_name: str,
    city: str,
) -> list[dict]:

    query = (
        f'"{business_name}" '
        f'"{city}" '
        "("
        '"new office" OR '
        '"new branch" OR '
        "expansion OR "
        "relocation OR "
        '"new facility"'
        ")"
    )

    return search_web(
        query,
        max_results=3,
    )


# =========================================================
# FUNDING
# =========================================================

def search_funding(
    business_name: str,
) -> list[dict]:

    query = (
        f'"{business_name}" '
        "("
        "funding OR investment OR "
        '"funding round" OR '
        '"raised"'
        ")"
    )

    return search_web(
        query,
        max_results=3,
    )


# =========================================================
# WORKPLACE / OFFICE SIGNALS
# =========================================================

def search_workplace_signals(
    business_name: str,
    city: str,
) -> list[dict]:

    query = (
        f'"{business_name}" '
        f'"{city}" '
        "("
        '"new office" OR '
        '"office space" OR '
        '"workspace" OR '
        '"headquarters" OR '
        '"team expansion"'
        ")"
    )

    return search_web(
        query,
        max_results=3,
    )


# =========================================================
# WEBSITE
# =========================================================

def search_website(
    website: str,
) -> list[dict]:

    if not website:
        return []

    website = website.replace(
        "https://",
        ""
    ).replace(
        "http://",
        ""
    ).rstrip("/")

    query = (
        f"site:{website} "
        "("
        "about OR services OR "
        "team OR contact"
        ")"
    )

    return search_web(
        query,
        max_results=4,
    )


# =========================================================
# COMPLETE RESEARCH
# =========================================================

def research_business(
    business_name: str,
    city: str,
    website: str | None = None,
) -> dict:

    print(
        f"\n[Tavily] Researching "
        f"{business_name} - {city}"
    )

    research = {

        "company_information":
            search_company(
                business_name,
                city,
            ),

        "recent_activity":
            search_recent_activity(
                business_name,
                city,
            ),

        "hiring_signals":
            search_hiring(
                business_name,
                city,
            ),

        "expansion_signals":
            search_expansion(
                business_name,
                city,
            ),

        "funding_signals":
            search_funding(
                business_name,
            ),

        "workplace_signals":
            search_workplace_signals(
                business_name,
                city,
            ),
    }

    if website:

        research["website"] = (
            search_website(
                website
            )
        )

    else:

        research["website"] = []

    return research


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    result = research_business(
        business_name="Apollo Hospitals",
        city="Hyderabad",
        website="https://www.apollohospitals.com/",
    )

    print("\n")
    print("=" * 60)
    print("TAVILY RESEARCH RESULTS")
    print("=" * 60)

    for section, results in result.items():

        print(f"\n--- {section.upper()} ---")

        if not results:
            print("No relevant information found.")
            continue

        for item in results:

            print("\nTitle:", item.get("title"))
            print("URL:", item.get("url"))
            print("Published:", item.get("published_date"))
            print("Evidence:", item.get("content", ""))

            print("-" * 50)