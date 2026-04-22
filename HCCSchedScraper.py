import csv
import os
from playwright.sync_api import sync_playwright

# -----------------------------
# CONFIG
# -----------------------------
SEARCH_URL = "https://colss-prod.ec.howardcc.edu/Student/Courses/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(BASE_DIR, "howardcc_schedule.csv")



# -----------------------------
# PARSE A SINGLE TABLE ROW
# -----------------------------
def parse_row(tr):
    tds = tr.query_selector_all("td.esg-table-body__td--section-table")

    def cell(i):
        return tds[i].inner_text().strip() if i < len(tds) else ""

    term = cell(0)
    status = cell(1)

    section = ""
    if len(tds) > 2:
        link = tds[2].query_selector("a")
        if link:
            section = link.inner_text().strip()

    title = cell(3)
    dates = cell(4)
    location = cell(5)

    methods = []
    if len(tds) > 6:
        for p in tds[6].query_selector_all("p"):
            txt = p.inner_text().strip()
            if txt:
                methods.append(txt)

    meetings = []
    if len(tds) > 7:
        for div in tds[7].query_selector_all("div"):
            txt = div.inner_text().strip()
            if txt:
                meetings.append(txt)

    instructors = []
    if len(tds) > 8:
        for span in tds[8].query_selector_all("span"):
            txt = span.inner_text().strip()
            if txt:
                instructors.append(txt)

    availability = cell(9)
    credits = cell(10)
    comments = cell(11)

    return {
        "Term": term,
        "Status": status,
        "Section": section,
        "Title": title,
        "Dates": dates,
        "Location": location,
        "InstructionalMethods": "; ".join(methods),
        "Meetings": "; ".join(meetings),
        "Instructors": "; ".join(instructors),
        "Availability": availability,
        "Credits": credits,
        "Comments": comments,
    }


# -----------------------------
# SCRAPE ONE SUBJECT
# -----------------------------
def scrape_single_subject(page, term, subject):
    print(f"Scraping {subject}...")

    page.goto(SEARCH_URL, wait_until="networkidle")

    # ✅ Select Term (correct as-is)
    page.get_by_label("Term").select_option(term)

    # ✅ WAIT for Subject dropdown, then select option
    subject_select = page.locator("#subject-0")
    subject_select.wait_for(state="visible")
    subject_select.select_option(subject)

    # ✅ Switch to Section Listing
    page.wait_for_selector("text=Section Listing")
    page.get_by_text("Section Listing", exact=True).click()

    # ✅ Click the correct Search button
    page.get_by_role("button", name="Search", exact=True).click()

    # ✅ Wait for results
    page.wait_for_selector("tr.esg-table-body__row", timeout=15000)

    rows = page.query_selector_all("tr.esg-table-body__row")
    return [parse_row(tr) for tr in rows]


# -----------------------------
# MAIN MULTI-SUBJECT SCRAPER
# -----------------------------
def scrape(term, subjects):
    all_records = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,   # ✅ OPEN BROWSER WINDOW
            slow_mo=400       # ✅ Slow enough to visually confirm behavior
        )
        context = browser.new_context()
        page = context.new_page()

        for subject in subjects:
            records = scrape_single_subject(page, term, subject)
            all_records.extend(records)

        # Keep browser open briefly for inspection
        page.wait_for_timeout(3000)
        browser.close()

    if not all_records:
        print("No classes found for any subject.")
        return

    fieldnames = list(all_records[0].keys())
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"✅ Saved {len(all_records)} total classes to {OUTPUT_CSV}")


# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    term = input("Enter term ID (e.g., 2026FA): ").strip()

    subjects = [
        s.strip().upper()
        for s in input(
            "Enter subjects (comma-separated, e.g., ENES, MATH, CMSY): "
        ).split(",")
    ]

    scrape(term, subjects)