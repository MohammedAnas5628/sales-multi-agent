from tools.research_tools import search_web


# =========================================================
# FUNDING SEARCH
# =========================================================

def search_funding(
    company_name: str,
    max_results: int = 10,
) -> list[dict]:

    if not company_name:
        return []

    query = (
        f'"{company_name}" '
        "(funding OR investment OR "
        '"raised" OR funding round)'
    )

    return search_web(
        query,
        max_results=max_results,
    )


# =========================================================
# SOURCE-SPECIFIC SEARCH
# =========================================================

def search_inc42(
    company_name: str,
) -> list[dict]:

    return search_web(
        f'site:inc42.com "{company_name}" funding',
        max_results=5,
    )


def search_yourstory(
    company_name: str,
) -> list[dict]:

    return search_web(
        f'site:yourstory.com "{company_name}" funding',
        max_results=5,
    )


def search_crunchbase(
    company_name: str,
) -> list[dict]:

    return search_web(
        f'site:crunchbase.com "{company_name}" funding',
        max_results=5,
    )


# =========================================================
# COMPLETE FUNDING RESEARCH
# =========================================================

def research_funding(
    company_name: str,
) -> dict:

    return {

        "general": search_funding(
            company_name
        ),

        "crunchbase": search_crunchbase(
            company_name
        ),

        "inc42": search_inc42(
            company_name
        ),

        "yourstory": search_yourstory(
            company_name
        ),

    }