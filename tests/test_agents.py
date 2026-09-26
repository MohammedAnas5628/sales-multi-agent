from tools.email_finder import (
    find_business_email,
    find_email_via_search,
)


def test_email_finder():

    business_name = "CS Coworking Spaces"
    city = "Hyderabad"
    website = "https://cscoworkingspaces.com/locations/shaikpet-2"

    print("\n" + "=" * 60)
    print("TESTING EMAIL FINDER")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Try website
    # --------------------------------------------------------

    print("\n[1] WEBSITE EMAIL SEARCH")

    email = find_business_email(website)

    print("Website Email:", email)

    # --------------------------------------------------------
    # 2. If no email, try Google search
    # --------------------------------------------------------

    if not email:

        print("\n[2] GOOGLE SEARCH EMAIL")

        email = find_email_via_search(
            business_name,
            city,
        )

        print("Search Email:", email)

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("EMAIL FINDER RESULT")
    print("=" * 60)

    if email:
        print("Email Found:", email)
    else:
        print("No email found.")


if __name__ == "__main__":
    test_email_finder()