from core.state import SalesState
from tools.excel_tools import export_results_to_excel


def excel_export_agent(state: SalesState) -> SalesState:
    """
    Export the final sales workflow results to Excel.
    """

    emails = state.get("emails", [])

    if not emails:
        print("\nNo email/lead results available for Excel export.")

        return {
            **state,
            "excel_file": "",
            "status": "excel_export_skipped",
        }

    # --------------------------------------------------------
    # Build lookup from researched/qualified leads
    # --------------------------------------------------------

    all_leads = (
        state.get("researched_leads", [])
        or state.get("qualified_leads", [])
        or []
    )

    lead_lookup = {}

    for lead in all_leads:
        business_name = lead.get("title")

        if business_name:
            lead_lookup[business_name] = lead

    # --------------------------------------------------------
    # Merge lead + email information
    # --------------------------------------------------------

    final_records = []

    for email_data in emails:

        business_name = email_data.get(
            "business_name"
        )

        lead = lead_lookup.get(
            business_name,
            {}
        )

        qualification_confidence = lead.get(
            "qualification_confidence"
        )

        qualification_reason = lead.get(
            "qualification_reason"
        )

        # Support both current/older research structures
        research = lead.get(
            "research",
            {}
        )

        record = {
            **email_data,

            # Lead information
            "category": lead.get(
                "categoryName"
            ),

            "city": lead.get(
                "city"
            ),

            # Qualification
            "qualification": True
            if qualification_reason
            else lead.get("qualification"),

            "qualification_reason":
                qualification_reason,

            "qualification_confidence":
                qualification_confidence,

            # Research
            "research_depth":
                lead.get("research_depth"),

            "business_summary":
                research.get("business_summary"),

            "industry":
                research.get("industry"),

            "business_activity_level":
                research.get(
                    "business_activity_level"
                ),

            "hiring_signals":
                research.get(
                    "hiring_signals"
                ),

            "expansion_signals":
                research.get(
                    "expansion_signals"
                ),

            "workplace_signals":
                research.get(
                    "workplace_signals"
                ),

            "chair_buying_signals":
                research.get(
                    "chair_buying_signals"
                ),
        }

        final_records.append(record)

    # --------------------------------------------------------
    # Export
    # --------------------------------------------------------

    excel_file = export_results_to_excel(
        emails=final_records
    )

    print(
        "\nExcel Export Completed:"
        f"\n{excel_file}"
    )

    return {
        **state,
        "emails": final_records,
        "excel_file": excel_file,
        "status": "excel_exported",
    }