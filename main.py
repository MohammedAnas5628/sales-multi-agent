import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from core.checkpointer import checkpointer
from core.state import SalesState

from agents.manager_agent import manager_agent
from agents.maps_agent import maps_agent
from agents.filtering_agent import filtering_agent
from agents.research_agent import research_agent
from agents.email_agent import email_agent
from agents.send_email_agent import send_email_agent
from agents.excel_export_agent import excel_export_agent


# ============================================================
# LANGGRAPH WORKFLOW
# ============================================================

workflow = StateGraph(SalesState)


# ============================================================
# NODES
# ============================================================

workflow.add_node(
    "manager",
    manager_agent,
)

workflow.add_node(
    "maps",
    maps_agent,
)

workflow.add_node(
    "filtering",
    filtering_agent,
)

workflow.add_node(
    "research",
    research_agent,
)

workflow.add_node(
    "email",
    email_agent,
)

workflow.add_node(
    "send_email",
    send_email_agent,
)

workflow.add_node(
    "excel_export",
    excel_export_agent,
)


# ============================================================
# MAIN FLOW
# ============================================================

workflow.add_edge(
    START,
    "manager",
)

workflow.add_edge(
    "manager",
    "maps",
)

workflow.add_edge(
    "maps",
    "filtering",
)

workflow.add_edge(
    "filtering",
    "research",
)

workflow.add_edge(
    "research",
    "email",
)

workflow.add_edge(
    "email",
    "send_email",
)

workflow.add_edge(
    "send_email",
    "excel_export",
)

workflow.add_edge(
    "excel_export",
    END,
)


# ============================================================
# COMPILE
# ============================================================

app = workflow.compile(
    checkpointer=checkpointer
)


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    user_request = input(
        "\nWhat leads do you want to find?\n> "
    )

    lead_limit_input = input(
        "\nHow many leads? (1-50)\n> "
    ).strip()

    try:

        lead_limit = int(
            lead_limit_input
        )

    except ValueError:

        lead_limit = 5

    lead_limit = max(
        1,
        min(
            lead_limit,
            50
        )
    )

    user_email = input(
        "\nEnter authenticated Gmail for this test:\n> "
    )

    thread_id = str(
        uuid.uuid4()
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    initial_state: SalesState = {

        "user_request":
            user_request,

        "user_email":
            user_email,

        "lead_limit":
            lead_limit,

        "status":
            "started",
    }

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STARTING SALES MULTI-AGENT WORKFLOW"
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # First run
    # --------------------------------------------------------

    result = app.invoke(
        initial_state,
        config=config,
    )

    # ========================================================
    # HUMAN APPROVAL
    # ========================================================

    while "__interrupt__" in result:

        print(
            "\n"
            + "=" * 60
        )

        print(
            "HUMAN APPROVAL REQUIRED"
        )

        print(
            "=" * 60
        )

        for item in result["__interrupt__"]:

            print(
                "\n"
                + str(item.value)
            )

        action = input(
            "\nChoose: approve / reject\n> "
        ).strip().lower()

        if action not in {
            "approve",
            "reject",
        }:

            print(
                "\nInvalid action."
            )

            continue

        result = app.invoke(
            Command(
                resume={
                    "action":
                        action
                }
            ),
            config=config,
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print(
        "\n"
        + "=" * 60
    )

    print(
        "WORKFLOW COMPLETED"
    )

    print(
        "=" * 60
    )

    print(
        "\nStatus:",
        result.get(
            "status"
        )
    )

    print(
        "Leads:",
        len(
            result.get(
                "leads",
                []
            )
        )
    )

    print(
        "Qualified:",
        len(
            result.get(
                "qualified_leads",
                []
            )
        )
    )

    print(
        "Emails:",
        len(
            result.get(
                "emails",
                []
            )
        )
    )

    print(
        "Excel File:",
        result.get(
            "excel_file"
        )
    )