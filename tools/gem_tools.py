from tools.research_tools import search_web


# =========================================================
# BUSINESS-SPECIFIC TENDERS
# =========================================================

def search_business_tenders(
    business_name: str,
    max_results: int = 10,
) -> list[dict]:

    if not business_name:
        return []

    query = (
        f'site:gem.gov.in '
        f'"{business_name}" '
        "(chair OR furniture OR "
        "seating OR office)"
    )

    return search_web(
        query,
        max_results=max_results,
    )


# =========================================================
# LOCATION FURNITURE TENDERS
# =========================================================

def search_location_tenders(
    location: str,
    max_results: int = 10,
) -> list[dict]:

    if not location:
        return []

    query = (
        f'site:gem.gov.in '
        f'"{location}" '
        '("office chair" OR '
        '"office furniture" OR '
        'seating)'
    )

    return search_web(
        query,
        max_results=max_results,
    )


# =========================================================
# COMPLETE GEM RESEARCH
# =========================================================

def research_gem(
    business_name: str,
    location: str,
) -> dict:

    return {

        "business_tenders":
            search_business_tenders(
                business_name
            ),

        "location_tenders":
            search_location_tenders(
                location
            ),

    }