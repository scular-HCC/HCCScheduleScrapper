import csv
import os
from playwright.sync_api import sync_playwright

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
SEARCH_URL = "https://colss-prod.ec.howardcc.edu/Student/Courses/"
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "howardcc_schedule.csv")

# -------------------------------------------------
# PARSE A SINGLE TABLE ROW
# -------------------------------------------------
def parse_row(tr):
    tds = tr.query_selector_all("td.esg-table-body__td--section-table")

    def cell(i):
        return tds[i].inner_text().strip() if i < len(tds) else ""

    section = ""
    if len(tds) > 2:
        link = tds[2].query_selector("a")
        section = link.inner_text().strip() if link else ""

    return {
        "Term": cell(0),
        "Status": cell(1),
        "Section": section,
        "Title": cell(3),
        "Dates": cell(4),
        "Location": cell(5),
        "InstructionalMethods": cell(6),
        "Meetings": cell(7),
        "Instructors": cell(8),
        "Availability": cell(9),
        "Credits": cell(10),
        "Comments": cell(11),
    }

# -------------------------------------------------
# PAGINATION HANDLER (NO RECURSION)
# -------------------------------------------------
def scrape_all_result_rows(page):
    all_rows = []
    page_num = 1

    while True:
        page.wait_for_selector("tr.esg-table-body__row", timeout=15000)

        rows = page.query_selector_all("tr.esg-table-body__row")
        print(f"    → Page {page_num}: {len(rows)} rows")

        all_rows.extend(rows)

        # ✅ Use the NEXT page button by ID (not aria-label)
        next_button = page.locator("#course-results-next-page")

        # Stop if next button does not exist or is disabled
        if next_button.count() == 0 or not next_button.is_enabled():
            break

        next_button.click()
        page.wait_for_timeout(1200)  # allow table refresh
        page_num += 1

    return all_rows

# -------------------------------------------------
# SCRAPE SINGLE SUBJECT
# -------------------------------------------------
def scrape_single_subject(page, term, subject):
    print(f"Scraping {subject}…")

    page.goto(SEARCH_URL, wait_until="networkidle")

    # Select term
    page.get_by_label("Term").select_option(term)

    # Subject dropdown
    subject_select = page.locator("#subject-0")
    subject_select.wait_for()
    subject_select.select_option(subject)

    # Use Section Listing
    page.get_by_text("Section Listing", exact=True).click()

    # Search
    page.get_by_role("button", name="Search", exact=True).click()

    # Pagination loop
    rows = scrape_all_result_rows(page)
    return [parse_row(tr) for tr in rows]

# -------------------------------------------------
# MAIN SCRAPER
# -------------------------------------------------
def scrape(term, subjects):
    all_records = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # change to True when stable
            slow_mo=300
        )
        context = browser.new_context()
        page = context.new_page()

        for subject in subjects:
            records = scrape_single_subject(page, term, subject)
            all_records.extend(records)

        browser.close()

    if not all_records:
        print("No classes found.")
        return

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_records[0].keys())
        writer.writeheader()
        writer.writerows(all_records)

    print(f"\n✅ Saved {len(all_records)} total classes to:")
    print(f"   {OUTPUT_CSV}")

# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------
if __name__ == "__main__":
    term = input("Enter term ID (e.g., 2026FA): ").strip()
    subjects = [
        s.strip().upper()
        for s in input(
            "Enter subjects (comma-separated, e.g., ENES, MATH, PHYS): "
        ).split(",")
    ]

    scrape(term, subjects)