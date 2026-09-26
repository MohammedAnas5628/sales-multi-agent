import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in .env"
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


MODEL = MODEL = "gemini-3.6-flash"


# =========================================================
# WEB RESEARCH
# =========================================================

def web_research(
    business_name: str,
    city: str | None = None,
) -> dict:

    if not business_name:
        return {
            "status": "error",
            "error": "Business name is required",
            "research": "",
            "sources": [],
        }

    location = city or ""

    prompt = f"""
Research the following business using current public web information.

Business:
{business_name}

Location:
{location}

Find useful information for B2B sales research.

Research:

1. What the business does
2. Industry
3. Main services/products
4. Target customers
5. Recent business activity
6. Recent news
7. Hiring activity
8. Expansion/new branches
9. Relocation or new office
10. Funding/investment
11. Recent business announcements
12. Website information
13. Any other useful business-development signals

IMPORTANT RULES:

- Use current public information.
- Separate confirmed facts from reasonable inferences.
- Never invent information.
- If information cannot be verified, say "Not found".
- Include the source URLs whenever available.
- Prefer recent information for activity, hiring,
  expansion, funding and news.
"""

    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        google_search=types.GoogleSearch()
                    )
                ],
                temperature=0.1,
            ),
        )

        sources = []

        # -------------------------------------------------
        # Extract grounding sources
        # -------------------------------------------------

        candidate = getattr(
            response,
            "candidates",
            None
        )

        if candidate:

            candidate = candidate[0]

            grounding_metadata = getattr(
                candidate,
                "grounding_metadata",
                None
            )

            if grounding_metadata:

                chunks = getattr(
                    grounding_metadata,
                    "grounding_chunks",
                    []
                )

                for chunk in chunks:

                    web = getattr(
                        chunk,
                        "web",
                        None
                    )

                    if web:

                        uri = getattr(
                            web,
                            "uri",
                            None
                        )

                        title = getattr(
                            web,
                            "title",
                            None
                        )

                        if uri:

                            sources.append({
                                "title": title,
                                "url": uri,
                            })

        return {
            "status": "success",
            "business_name": business_name,
            "city": city,
            "research": response.text,
            "sources": sources,
        }

    except Exception as e:

        print(
            f"[Google Research] Error: {e}"
        )

        return {
            "status": "error",
            "business_name": business_name,
            "city": city,
            "research": "",
            "sources": [],
            "error": str(e),
        }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    result = web_research(
        business_name=(
            "V Care N Cure "
            "Multi-speciality "
            "Dental Clinic"
        ),
        city="Hyderabad",
    )

    print("\n" + "=" * 60)
    print("GOOGLE WEB RESEARCH")
    print("=" * 60)

    print(
        "\nStatus:",
        result["status"]
    )

    print(
        "\nResearch:\n",
        result["research"]
    )

    print(
        "\nSources:"
    )

    for source in result["sources"]:

        print(
            "-",
            source["title"],
            ":",
            source["url"]
        )