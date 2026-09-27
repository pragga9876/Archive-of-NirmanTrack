from pathlib import Path
import requests


# ============================================================
# CONFIGURATION
# ============================================================

TEST_URL = (
    "https://paimana-proj.mospi.gov.in/"
    "ReportPage/ViewPdf"
    "?id=1219"
    "&path=Content%5CArchiveReport%5Cflash%5C2007-08%5CFR_MAY_2007.pdf"
)

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "data" / "temp_pdf_test"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = OUTPUT_DIR / "test_2007_report.pdf"


# ============================================================
# DOWNLOAD TEST
# ============================================================

print("\n" + "=" * 80)
print("TESTING HISTORICAL PDF ACCESS")
print("=" * 80)

print("\nRequest URL:")
print(TEST_URL)

print("\nSending request...\n")

headers = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 "
        "Safari/537.36"
    )
}


try:

    response = requests.get(
        TEST_URL,
        headers=headers,
        timeout=60,
        allow_redirects=True
    )

    print("Status Code:")
    print(response.status_code)

    print("\nFinal URL:")
    print(response.url)

    print("\nContent-Type:")
    print(
        response.headers.get(
            "Content-Type",
            "UNKNOWN"
        )
    )

    print("\nContent Length:")
    print(
        len(response.content),
        "bytes"
    )

    print("\nResponse Headers:")

    for key, value in response.headers.items():
        print(f"{key}: {value}")


    # ========================================================
    # CHECK RESPONSE
    # ========================================================

    if response.status_code != 200:

        print("\n[ERROR] Request failed.")

        exit()


    # ========================================================
    # PDF SIGNATURE CHECK
    # ========================================================

    if response.content.startswith(b"%PDF"):

        print("\n[SUCCESS] Response is a real PDF.")

        with open(
            OUTPUT_FILE,
            "wb"
        ) as file:

            file.write(
                response.content
            )

        print("\nPDF temporarily saved:")
        print(OUTPUT_FILE)

        print(
            "\nFile size:"
        )

        print(
            round(
                OUTPUT_FILE.stat().st_size / 1024,
                2
            ),
            "KB"
        )

    else:

        print(
            "\n[WARNING] Response does not appear "
            "to be a raw PDF."
        )

        print(
            "\nFirst 500 bytes of response:"
        )

        print(
            response.content[:500]
        )


except requests.exceptions.RequestException as error:

    print("\n[REQUEST ERROR]")

    print(error)


print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)