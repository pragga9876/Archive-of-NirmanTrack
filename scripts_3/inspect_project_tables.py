import pdfplumber
import requests
from io import BytesIO
from pathlib import Path


URL = (
    "https://paimana-proj.mospi.gov.in/"
    "ReportPage/ViewPdf?"
    "id=1151&"
    "path=Content\\ArchiveReport\\flash\\2025-26\\FRApril2025.pdf"
)


print("=" * 100)
print("INSPECTING PROJECT TABLE STRUCTURE")
print("=" * 100)

print("\nDownloading PDF...")

response = requests.get(URL, timeout=60)
response.raise_for_status()

print(f"Downloaded: {len(response.content) / (1024 * 1024):.2f} MB")


pdf_file = BytesIO(response.content)


with pdfplumber.open(pdf_file) as pdf:

    print(f"\nTotal Pages: {len(pdf.pages)}")

    # Based on contents:
    # Table 6 begins around PDF page 39.
    pages_to_check = [
        38,
        39,
        40,
        41,
        42
    ]

    for page_number in pages_to_check:

        if page_number >= len(pdf.pages):
            continue

        print("\n")
        print("=" * 100)
        print(f"PDF PAGE {page_number + 1}")
        print("=" * 100)

        page = pdf.pages[page_number]

        text = page.extract_text()

        if text:

            print("\nTEXT:")
            print("-" * 100)

            print(text[:5000])

        else:

            print("\nNO TEXT EXTRACTED.")

        tables = page.extract_tables()

        print("\n")
        print(f"TABLES DETECTED: {len(tables)}")

        for table_index, table in enumerate(tables):

            print("\n")
            print("-" * 100)
            print(f"TABLE {table_index + 1}")
            print("-" * 100)

            for row in table[:10]:

                print(row)


print("\n")
print("=" * 100)
print("DONE")
print("=" * 100)