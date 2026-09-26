import re
from urllib.parse import urlparse

from core.apify_token_manager import apify_manager


WEBSITE_CONTACT_ACTOR = (
    "theprojectdesk/website-contact-extractor"
)

GOOGLE_SEARCH_ACTOR = (
    "apify/google-search-scraper"
)


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+"
    r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


IGNORED_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "tiktok.com",
    "pinterest.com",
}


def _clean_email(email: str) -> str | None:
    email = (
        email
        .strip()
        .lower()
        .strip(" <>[](){}\"',;:")
    )

    if not EMAIL_PATTERN.fullmatch(email):
        return None

    domain = email.split("@")[-1].lower()

    if domain in IGNORED_DOMAINS:
        return None

    return email


def _extract_emails_from_text(text: str) -> list[str]:
    if not text:
        return []

    found = EMAIL_PATTERN.findall(text)

    emails = []

    for email in found:
        cleaned = _clean_email(email)

        if cleaned and cleaned not in emails:
            emails.append(cleaned)

    return emails


def find_business_email(
    website: str,
) -> str | None:

    if not website:
        return None

    parsed = urlparse(website)

    if not parsed.scheme:
        website = "https://" + website

    print(
        f"[Email Finder] Website: {website}"
    )

    run_input = {
        "startUrls": [
            {
                "url": website
            }
        ],
    }

    try:
        client, run = apify_manager.run_actor(
            WEBSITE_CONTACT_ACTOR,
            run_input,
        )

        dataset_items = (
            client
            .dataset(run.default_dataset_id)
            .iterate_items()
        )

        for item in dataset_items:

            text = str(item)

            emails = _extract_emails_from_text(text)

            if emails:
                print(
                    "[Email Finder] Found: "
                    f"{emails[0]}"
                )

                return emails[0]

    except Exception as error:

        print(
            "[Email Finder] Website actor failed: "
            f"{error}"
        )

    return None


def find_email_via_search(
    business_name: str,
    city: str | None = None,
) -> str | None:

    search_query = (
        f'"{business_name}" "email"'
    )

    if city:
        search_query += (
            f' "{city}"'
        )

    # Force string explicitly
    search_query = str(search_query)

    print(
        f"[Email Finder] Search: {search_query}"
    )

    run_input = {
        "queries": search_query,
        "maxPagesPerQuery": 1,
    }

    # DEBUG
    print(
        "[Email Finder] DEBUG run_input:",
        run_input
    )

    print(
        "[Email Finder] DEBUG queries type:",
        type(run_input["queries"])
    )

    try:

        client, run = apify_manager.run_actor(
            GOOGLE_SEARCH_ACTOR,
            run_input,
        )

        dataset_items = (
            client
            .dataset(run.default_dataset_id)
            .iterate_items()
        )

        for item in dataset_items:

            text = str(item)

            emails = _extract_emails_from_text(
                text
            )

            if emails:

                print(
                    "[Email Finder] Found: "
                    f"{emails[0]}"
                )

                return emails[0]

    except Exception as error:

        print(
            "[Email Finder] Google search actor failed: "
            f"{error}"
        )

    return None