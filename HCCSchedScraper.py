import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service

# -----------------------------
# CONFIG
# -----------------------------
EDGE_DRIVER_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe"
SEARCH_URL = "https://colss-prod.ec.howardcc.edu/Student/Courses/Search"
OUTPUT_CSV = "howardcc_schedule.csv"

service = Service(EDGE_DRIVER_PATH)


# -----------------------------
# PARSE A SINGLE TABLE ROW
# -----------------------------
def parse_row(tr):
    tds = tr.find_elements(By.CSS_SELECTOR, "td.esg-table-body__td--section-table")

    def cell(i):
        return tds[i].text.strip() if i < len(tds) else ""

    term = cell(0)
    status = cell(1)

    section = ""
    if len(tds) > 2:
        link = tds[2].find_element(By.TAG_NAME, "a")
        section = link.text.strip()

    title = cell(3)
    dates = cell(4)
    location = cell(5)

    # Instructional methods
    methods = []
    if len(tds) > 6:
        for p in tds[6].find_elements(By.TAG_NAME, "p"):
            txt = p.text.strip()
            if txt:
                methods.append(txt)

    # Meetings
    meetings = []
    if len(tds) > 7:
        for div in tds[7].find_elements(By.TAG_NAME, "div"):
            txt = div.text.strip()
            if txt:
                meetings.append(txt)

    # Instructors
    instructors = []
    if len(tds) > 8:
        for span in tds[8].find_elements(By.TAG_NAME, "span"):
            txt = span.text.strip()
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
def scrape_single_subject(term, subject):
    print(f"Scraping {subject}...")

    driver = webdriver.Edge(service=service)
    driver.get(SEARCH_URL)

    wait = WebDriverWait(driver, 20)

    # Select term (adjust selector if needed)
    term_select = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='terms']"))
    )
    Select(term_select).select_by_value(term)

    # Enter subject (adjust selector if needed)
    subject_input = driver.find_element(By.CSS_SELECTOR, "input[name='keywordComponents[0].subject']")
    subject_input.clear()
    subject_input.send_keys(subject)

    # Click search
    search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    search_button.click()

    # Wait for results
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.esg-table-body__row")))
    time.sleep(1)

    rows = driver.find_elements(By.CSS_SELECTOR, "tr.esg-table-body__row")
    records = [parse_row(tr) for tr in rows]

    driver.quit()
    return records


# -----------------------------
# MAIN MULTI-SUBJECT SCRAPER
# -----------------------------
def scrape(term, subjects):
    all_records = []

    for subject in subjects:
        records = scrape_single_subject(term, subject)
        all_records.extend(records)

    if not all_records:
        print("No classes found for any subject.")
        return

    fieldnames = list(all_records[0].keys())
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"Saved {len(all_records)} total classes to {OUTPUT_CSV}")


# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    term = input("Enter term ID (e.g., 2026FA): ").strip()

    subjects = [
        s.strip().upper()
        for s in input("Enter subjects (comma-separated, e.g., ENES, MATH, CMSY): ").split(",")
    ]

    scrape(term, subjects)