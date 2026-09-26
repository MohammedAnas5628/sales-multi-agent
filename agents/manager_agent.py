from pydantic import BaseModel, Field

from core.llm import llm
from core.state import SalesState


# ============================================================
# MANAGER OUTPUT
# ============================================================

class ManagerPlan(BaseModel):

    business_type: str = Field(
        description="The type of business the user wants as leads."
    )

    location: str = Field(
        description="The target city or location from the user's request."
    )

    search_query: str = Field(
        description="A concise search query for finding the requested businesses."
    )

    workflow_plan: list[str] = Field(
        description=(
            "Ordered workflow stages. "
            "Use: maps, filtering, research, email, approval, send, excel."
        )
    )


structured_llm = llm.with_structured_output(ManagerPlan)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are the Manager Agent of a B2B sales automation system.

Your job is to understand the user's lead-generation request and
create a clean execution plan.

The workflow stages are:

1. maps
2. filtering
3. research
4. email
5. approval
6. send
7. excel


IMPORTANT DISTINCTION:

business_type means the TYPE OF BUSINESS the USER wants as leads.

The product being sold is office chairs.

The product being sold and the requested lead business type are
TWO COMPLETELY DIFFERENT THINGS.

NEVER use the product being sold as business_type.


Examples:

User request:
"coworking spaces in Hyderabad"

Correct:
business_type = "coworking spaces"
location = "Hyderabad"
search_query = "coworking spaces"


User request:
"dental clinics in Hyderabad"

Correct:
business_type = "dental clinics"
location = "Hyderabad"
search_query = "dental clinics"


User request:
"gyms in Bangalore"

Correct:
business_type = "gyms"
location = "Bangalore"
search_query = "gyms"


User request:
"restaurants in Mumbai"

Correct:
business_type = "restaurants"
location = "Mumbai"
search_query = "restaurants"


NEVER do this:

business_type = "office chairs"
business_type = "office furniture"
business_type = "B2B - Office Furniture/Furniture Sales"

Those describe the PRODUCT being sold, not the businesses being searched for.


Your responsibilities:

1. Extract the requested business type from the user's request.
2. Extract the requested location.
3. Create a concise search query for finding those businesses.
4. Create the normal workflow plan.

Do not invent missing information.

The normal workflow is:

maps → filtering → research → email → approval → send → excel
"""


# ============================================================
# MANAGER AGENT
# ============================================================

def manager_agent(
    state: SalesState,
) -> SalesState:

    user_request = state.get(
        "user_request",
        "",
    )

    prompt = f"""
Understand this sales-lead request:

{user_request}

Extract the business type and location requested by the user.

Remember:

- business_type = target lead business
- location = target lead location
- search_query = query used to find those businesses
- office chairs = product being sold, NOT business_type

Create the execution plan.
"""

    print("\n" + "=" * 60)
    print("MANAGER AGENT")
    print("=" * 60)

    try:

        result = structured_llm.invoke(
            [
                (
                    "system",
                    SYSTEM_PROMPT,
                ),
                (
                    "human",
                    prompt,
                ),
            ]
        )

        # ----------------------------------------------------
        # Normalize workflow plan
        # ----------------------------------------------------

        allowed_stages = {
            "maps",
            "filtering",
            "research",
            "email",
            "approval",
            "send",
            "excel",
        }

        workflow_plan = [
            stage.strip().lower()
            for stage in result.workflow_plan
            if stage.strip().lower() in allowed_stages
        ]

        if not workflow_plan:
            workflow_plan = [
                "maps",
                "filtering",
                "research",
                "email",
                "approval",
                "send",
                "excel",
            ]

        # ----------------------------------------------------
        # Safety check:
        # business_type must NOT be the product
        # ----------------------------------------------------

        invalid_business_types = {
            "office chairs",
            "office chair",
            "office furniture",
            "b2b - office furniture/furniture sales",
            "furniture sales",
        }

        business_type = result.business_type.strip()
        location = result.location.strip()
        search_query = result.search_query.strip()

        if business_type.lower() in invalid_business_types:

            print(
                "WARNING: Manager returned product as business_type."
            )

            print(
                "Falling back to user's request for business type."
            )

            # Try to recover common "business type in location" format.
            request_text = user_request.strip()

            if " in " in request_text.lower():

                parts = request_text.rsplit(
                    " in ",
                    1,
                )

                if len(parts) == 2:

                    extracted_business = parts[0].strip()
                    extracted_location = parts[1].strip()

                    if extracted_business:
                        business_type = extracted_business

                    if extracted_location:
                        location = extracted_location

                    search_query = business_type

        # ----------------------------------------------------
        # Final logging
        # ----------------------------------------------------

        print(
            "Business:",
            business_type,
        )

        print(
            "Location:",
            location,
        )

        print(
            "Search Query:",
            search_query,
        )

        print(
            "Workflow Plan:",
            workflow_plan,
        )

        # ----------------------------------------------------
        # Return updated state
        # ----------------------------------------------------

        return {
            **state,

            "business_type": business_type,

            "location": location,

            "search_query": search_query,

            "workflow_plan": workflow_plan,

            "current_stage": "maps",

            "retry_counts": {
                "maps": 0,
                "filtering": 0,
                "research": 0,
                "email": 0,
            },

            "status": "manager_completed",
        }

    except Exception as e:

        print(
            f"Manager failed: {e}"
        )

        return {
            **state,
            "error": str(e),
            "status": "manager_failed",
        }