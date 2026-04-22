import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import random
import re
import os

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "howardcc_schedule.csv")
PDF_OUTPUT = os.path.join(BASE_DIR, "weekly_schedule.pdf")

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

DAY_MAP = {
    "M": "Mon",
    "T": "Tue",
    "W": "Wed",
    "Th": "Thu",
    "F": "Fri"
}

# -----------------------------
# PARSE MEETINGS
# -----------------------------
def parse_meetings(meeting_cell, section):
    meetings = []
    lines = meeting_cell.replace(";", "\n").splitlines()

    time_pattern = re.compile(
        r"([MTWThF, ]+)\s+"
        r"(\d{1,2}:\d{2})"
        r"(?:\s*(AM|PM))?"
        r"\s*-\s*"
        r"(\d{1,2}:\d{2})\s*(AM|PM)"
    )

    for line in lines:
        m = time_pattern.search(line)
        if not m:
            continue

        days_raw, start, start_ampm, end, end_ampm = m.groups()
        if not start_ampm:
            start_ampm = end_ampm

        start_dt = datetime.strptime(f"{start} {start_ampm}", "%I:%M %p")
        end_dt = datetime.strptime(f"{end} {end_ampm}", "%I:%M %p")

        for d in days_raw.replace(",", "").split():
            day = DAY_MAP.get(d)
            if day:
                meetings.append({
                    "section": section,
                    "day": day,
                    "start": start_dt,
                    "end": end_dt
                })

    return meetings

# -----------------------------
# CONFLICT DETECTION
# -----------------------------
def detect_conflicts(meetings):
    conflicts = []
    for i in range(len(meetings)):
        a = meetings[i]
        for j in range(i + 1, len(meetings)):
            b = meetings[j]
            if a["day"] != b["day"] or a["section"] == b["section"]:
                continue
            if max(a["start"], b["start"]) < min(a["end"], b["end"]):
                conflicts.append((a, b))
    return conflicts

# -----------------------------
# DRAW CONFLICT OVERLAY
# -----------------------------
def draw_conflict_overlays(conflicts, ax):
    for a, b in conflicts:
        x = DAYS.index(a["day"])
        start = max(a["start"], b["start"])
        end = min(a["end"], b["end"])

        y = start.hour + start.minute / 60
        h = (end - start).seconds / 3600

        ax.add_patch(
            plt.Rectangle(
                (x, y),
                0.9,
                h,
                facecolor="red",
                alpha=0.35,
                zorder=10
            )
        )

# -----------------------------
# DRAW CALENDAR + EXPORT PDF
# -----------------------------
def draw_calendar(selected_sections, df):
    all_meetings = []
    colors = {}

    with PdfPages(PDF_OUTPUT) as pdf:

        # ---------- PAGE 1: CALENDAR ----------
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim(0, 5)
        ax.set_xticks(range(5))
        ax.set_xticklabels(DAYS)

        ax.set_ylim(8, 22)  # ascending time
        ax.set_yticks(range(8, 23))
        ax.set_ylabel("Time")
        ax.invert_yaxis()


        ax.grid(True)

        for section in selected_sections:
            row = df[df["Section"] == section].iloc[0]
            meetings = parse_meetings(row["Meetings"], section)
            all_meetings.extend(meetings)

            colors.setdefault(section, (
                random.random(),
                random.random(),
                random.random()
            ))

            for m in meetings:
                x = DAYS.index(m["day"])
                y = m["start"].hour + m["start"].minute / 60
                h = (m["end"] - m["start"]).seconds / 3600

                ax.add_patch(
                    plt.Rectangle(
                        (x, y),
                        0.9,
                        h,
                        facecolor=colors[section],
                        alpha=0.8
                    )
                )
                ax.text(
                    x + 0.45,
                    y + h / 2,
                    section,
                    ha="center",
                    va="center",
                    fontsize=8
                )

        conflicts = detect_conflicts(all_meetings)
        draw_conflict_overlays(conflicts, ax)

        ax.set_title("Weekly Class Schedule")
        plt.tight_layout()
        pdf.savefig(fig)
        plt.show()
        plt.close(fig)

        # ---------- PAGE 2: CONFLICT REPORT ----------
        fig2, ax2 = plt.subplots(figsize=(8.5, 11))
        ax2.axis("off")

        y = 0.95
        ax2.text(0.05, y, "Schedule Conflict Report", fontsize=16, weight="bold")
        y -= 0.05

        if not conflicts:
            ax2.text(0.05, y, "✅ No conflicts detected.")
        else:
            for a, b in conflicts:
                ax2.text(
                    0.05,
                    y,
                    f"❌ {a['section']} conflicts with {b['section']} on "
                    f"{a['day']} {a['start'].strftime('%I:%M %p')}–"
                    f"{a['end'].strftime('%I:%M %p')}"
                )
                y -= 0.035

        pdf.savefig(fig2)
        plt.close(fig2)

    print(f"📄 PDF exported: {PDF_OUTPUT}")

# -----------------------------
# GUI
# -----------------------------
def run_gui():
    df = pd.read_csv(CSV_PATH)
    sections = sorted(df["Section"].unique())

    root = tk.Tk()
    root.title("HCC Weekly Schedule Builder")

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Select Classes").pack(anchor="w")

    listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=40, height=25)
    for s in sections:
        listbox.insert(tk.END, s)
    listbox.pack()

    def generate():
        selected = [listbox.get(i) for i in listbox.curselection()]
        if selected:
            draw_calendar(selected, df)

    ttk.Button(frame, text="Generate Calendar & Export PDF", command=generate).pack(pady=10)

    root.mainloop()

# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    run_gui()