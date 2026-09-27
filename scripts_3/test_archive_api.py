import requests
import json


BASE_URL = "https://paimana-proj.mospi.gov.in/ReportPage"


# ============================================================
# HELPER FUNCTION
# ============================================================

def print_response(title, response):
    print("\n")
    print("=" * 100)
    print(title)
    print("=" * 100)

    print("\nStatus:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("\nFinal URL:")
    print(response.url)

    print("\nResponse preview:")

    content_type = response.headers.get("Content-Type", "")

    if "application/json" in content_type:

        try:
            data = response.json()
            print(json.dumps(data, indent=2)[:5000])
        except Exception:
            print(response.text[:5000])

    else:
        print(response.text[:5000])


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
})


# ============================================================
# 1. GET FINANCIAL YEARS
# ============================================================

print("\n")
print("#" * 100)
print("TESTING ARCHIVE API")
print("#" * 100)


url = f"{BASE_URL}/GetArchiveFinancialYearList"

try:

    response = session.get(
        url,
        timeout=30
    )

    print_response(
        "GET ARCHIVE FINANCIAL YEAR LIST",
        response
    )

except Exception as e:

    print("\nERROR:")
    print(e)


# ============================================================
# 2. TEST ARCHIVE REPORT
#
# Controller signature discovered:
#
# ArchiveReport(
#     System.String,
#     Int32,
#     Int32,
#     System.String
# )
#
# IMPORTANT:
# The server specifically calls the parameter:
#
# quater
#
# Yes, it is misspelled on the server.
# ============================================================


tests = [

    {
        "name": "MONTHLY REPORT TEST",
        "params": {
            "type": "N",
            "month": 1,
            "quater": 0,
            "ReportType": "N"
        }
    },


    {
        "name": "MONTHLY REPORT TEST - MONTH 2",
        "params": {
            "type": "N",
            "month": 2,
            "quater": 0,
            "ReportType": "N"
        }
    },


    {
        "name": "QUARTERLY REPORT TEST",
        "params": {
            "type": "Q",
            "month": 0,
            "quater": 1,
            "ReportType": "Q"
        }
    }

]


# ============================================================
# RUN TESTS
# ============================================================

url = f"{BASE_URL}/ArchiveReport"


for test in tests:

    print("\n")
    print("#" * 100)
    print(test["name"])
    print("#" * 100)

    print("\nParameters:")

    for key, value in test["params"].items():
        print(f"{key}: {value}")


    try:

        response = session.get(
            url,
            params=test["params"],
            timeout=30
        )

        print_response(
            test["name"],
            response
        )


    except Exception as e:

        print("\nERROR:")
        print(e)


print("\n")
print("#" * 100)
print("TEST COMPLETE")
print("#" * 100)