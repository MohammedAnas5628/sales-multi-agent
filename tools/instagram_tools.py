import os

from dotenv import load_dotenv
from apify_client import ApifyClient


load_dotenv()

APIFY_API_TOKEN = os.getenv(
    "APIFY_API_TOKEN"
)

INSTAGRAM_ACTOR_ID = os.getenv(
    "APIFY_INSTAGRAM_ACTOR_ID"
)

if not APIFY_API_TOKEN:
    raise ValueError(
        "APIFY_API_TOKEN not found in .env"
    )

client = ApifyClient(
    APIFY_API_TOKEN
)


# =========================================================
# PROFILE POSTS
# =========================================================

def get_instagram_posts(
    username: str,
    results_limit: int = 10,
) -> list[dict]:

    if not username:
        return []

    if not INSTAGRAM_ACTOR_ID:

        print(
            "APIFY_INSTAGRAM_ACTOR_ID "
            "not configured."
        )

        return []

    username = username.lstrip("@")

    try:

        run = client.actor(
            INSTAGRAM_ACTOR_ID
        ).call(
            run_input={
                "directUrls": [
                    f"https://www.instagram.com/{username}/"
                ],
                "resultsType": "posts",
                "resultsLimit": results_limit,
            }
        )

        dataset_id = (
            run.default_dataset_id
        )

        posts = (
            client.dataset(
                dataset_id
            )
            .list_items()
            .items
        )

        return posts[:results_limit]

    except Exception as e:

        print(
            f"[instagram_tools] "
            f"Instagram failed: {e}"
        )

        return []


# =========================================================
# ACTIVITY EVIDENCE
# =========================================================

def build_social_evidence(
    posts: list[dict],
) -> dict:

    evidence = []

    for post in posts:

        evidence.append({

            "caption": post.get(
                "caption"
            ),

            "timestamp": (
                post.get("timestamp")
                or post.get("takenAt")
            ),

            "likes": (
                post.get("likesCount")
                or post.get("likes")
            ),

            "comments": (
                post.get("commentsCount")
                or post.get("comments")
            ),

            "url": (
                post.get("url")
                or post.get("postUrl")
            ),

        })

    return {
        "post_count": len(posts),
        "evidence": evidence,
    }