from storage.excel import export_sales_results


def export_results_to_excel(
    emails: list[dict],
    filename: str | None = None,
) -> str:
    """
    Public tool used by the LangGraph workflow
    to export final sales results.
    """

    if not emails:
        print(
            "\nNo email/lead results available "
            "for Excel export."
        )

        return ""

    return export_sales_results(
        emails=emails,
        filename=filename,
    )