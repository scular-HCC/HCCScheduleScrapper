/*************************************************
 * CONSTANTS & GLOBAL STATE
 *************************************************/
const DAY_MAP = { M: 1, T: 2, W: 3, Th: 4, F: 5 };
const DAY_NAME = {
  1: "Monday",
  2: "Tuesday",
  3: "Wednesday",
  4: "Thursday",
  5: "Friday"
};

let classes = [];
let calendar = null;

/*************************************************
 * DOM ELEMENTS
 *************************************************/
const fileInput   = document.getElementById("csvInput");

const classList  = document.getElementById("classList");
const resetBtn   = document.getElementById("resetBtn");
const buildBtn    = document.getElementById("buildBtn");
const pdfBtn      = document.getElementById("pdfBtn");
const conflictDiv = document.getElementById("conflicts");

/*************************************************
 * LOAD CSV VIA FILE PICKER (PapaParse)
 *************************************************/
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;

  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      classes = results.data.filter(
        row => row.Section && row.Meetings
      );
      populateClassList();
    },
    error: (err) => {
      alert("CSV parse error: " + err.message);
    }
  });
});

/*************************************************
 * POPULATE CLASS SELECT LIST
 *************************************************/
function populateClassList() {
  classList.innerHTML = "";

  classes.forEach(c => {
    const label = document.createElement("label");
    label.className = "class-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = c.Section;

    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(" " + c.Section));

    classList.appendChild(label);
  });

  buildBtn.disabled = false;
  resetBtn.disabled = false;
  pdfBtn.disabled = false;
}

/*************************************************
 * TIME CONVERSION (AM/PM -> 24H)
 *************************************************/
function to24Hour(time, ampm) {
  let [h, m] = time.split(":").map(Number);
  if (ampm === "PM" && h < 12) h += 12;
  if (ampm === "AM" && h === 12) h = 0;
  return `${h.toString().padStart(2, "0")}:${m
    .toString()
    .padStart(2, "0")}`;
}

/*************************************************
 * PARSE & DEDUPLICATE MEETINGS
 *************************************************/
function parseMeetings(text, section) {
  const meetings = [];
  const seen = new Set();

  const regex =
    /([MTWThF, ]+)\s+(\d{1,2}:\d{2})(?:\s*(AM|PM))?\s*-\s*(\d{1,2}:\d{2})\s*(AM|PM)/gi;

  let match;
  while ((match = regex.exec(text)) !== null) {
    let [, days, start, sAmpm, end, eAmpm] = match;
    if (!sAmpm) sAmpm = eAmpm;

    const start24 = to24Hour(start, sAmpm);
    const end24   = to24Hour(end, eAmpm);

    days.replace(/,/g, "").split(/\s+/).forEach(d => {
      const dayNum = DAY_MAP[d];
      if (!dayNum) return;

      const key = `${section}|${dayNum}|${start24}|${end24}`;
      if (seen.has(key)) return;
      seen.add(key);

      meetings.push({
        section,
        day: dayNum,
        start: start24,
        end: end24
      });
    });
  }

  return meetings;
}

/*************************************************
 * CONFLICT DETECTION
 *************************************************/
function detectConflicts(meetings) {
  const conflicts = [];

  for (let i = 0; i < meetings.length; i++) {
    for (let j = i + 1; j < meetings.length; j++) {
      const a = meetings[i];
      const b = meetings[j];

      if (a.day !== b.day || a.section === b.section) continue;

      if (a.start < b.end && b.start < a.end) {
        conflicts.push([a, b]);
      }
    }
  }

  return conflicts;
}

/*************************************************
 * Reset BUTTON
 *************************************************/
resetBtn.addEventListener("click", () => {
  // Uncheck all boxes
  classList
    .querySelectorAll("input[type=checkbox]")
    .forEach(cb => cb.checked = false);

  // Clear conflicts sidebar
  conflictDiv.innerHTML = "";
  conflictDiv.style.color = "";

  // Clear calendar
  if (calendar) {
    calendar.destroy();
    calendar = null;
  }
});


/*************************************************
 * BUILD SCHEDULE BUTTON
 *************************************************/
buildBtn.addEventListener("click", () => {
  conflictDiv.innerHTML = "";

  const selectedSections = [
  ...classList.querySelectorAll("input[type=checkbox]:checked")
].map(cb => cb.value);

  let meetings = [];
  selectedSections.forEach(sec => {
    const row = classes.find(c => c.Section === sec);
    if (!row) return;
    meetings.push(...parseMeetings(row.Meetings, sec));
  });

  const conflicts = detectConflicts(meetings);

  renderCalendar(meetings, conflicts);
  renderConflictSidebar(conflicts);
});

/*************************************************
 * SECTION COLOR MAP (NO RED TONES)
 *************************************************/
const sectionColors = {};

// Allowed hue ranges (exclude reds ~340–20°)
const SAFE_HUE_RANGES = [
  [30, 140],   // yellow → green
  [160, 260],  // teal → blue
  [280, 330]   // purple → pink (no red)
];

function getSectionColor(section) {
  if (!sectionColors[section]) {
    const range =
      SAFE_HUE_RANGES[Math.floor(Math.random() * SAFE_HUE_RANGES.length)];

    const hue =
      Math.floor(Math.random() * (range[1] - range[0])) + range[0];

    sectionColors[section] = `hsl(${hue}, 65%, 70%)`;
  }

  return sectionColors[section];
}


/*************************************************
 * RENDER FULLCALENDAR + CONFLICT OVERLAYS
 *************************************************/
function renderCalendar(meetings, conflicts) {
  if (calendar) calendar.destroy();

  const classEvents = [];
  const conflictOverlays = [];

  meetings.forEach(m => {
  const color = getSectionColor(m.section);

  classEvents.push({
    title: m.section,
    daysOfWeek: [m.day],
    startTime: m.start,
    endTime: m.end,

    // ✅ Per-class color
    backgroundColor: color,
    borderColor: color,
    textColor: "#000"
  });
});

  conflicts.forEach(([a, b]) => {
  conflictOverlays.push({
    title: "CONFLICT",
    daysOfWeek: [a.day],
    startTime: a.start > b.start ? a.start : b.start,
    endTime: a.end < b.end ? a.end : b.end,

    overlap: true,
    editable: false,
    interactive: false,

    // ✅ treat as normal event
    display: "block",

    // ✅ use CSS for styling
    classNames: ["conflict-overlay"]
  });
});

  calendar = new FullCalendar.Calendar(
    document.getElementById("calendar"),
    {
      initialView: "timeGridWeek",
      allDaySlot: false,
      weekends: false,
      height: "auto",
      slotMinTime: "08:00:00",
      slotMaxTime: "22:00:00",
      events: [...classEvents, ...conflictOverlays]
    }
  );

  calendar.render();
}

/*************************************************
 * CONFLICT WARNINGS SIDEBAR
 *************************************************/
function renderConflictSidebar(conflicts) {
  if (!conflicts.length) {
    conflictDiv.style.color = "green";
    conflictDiv.innerHTML = "✅ No conflicts detected.";
    return;
  }

  conflictDiv.style.color = "red";
  conflictDiv.innerHTML = "<strong>⚠ Conflicts:</strong>";

  conflicts.forEach(([a, b]) => {
    conflictDiv.innerHTML += `
      <div style="margin-top:6px;">
        ❌ ${a.section} & ${b.section}<br>
        ${DAY_NAME[a.day]} ${a.start}–${a.end}
      </div>
    `;
  });
}

/*************************************************
 * PDF EXPORT HANDLER (GUARANTEED DOWNLOAD)
 *************************************************/
pdfBtn.addEventListener("click", async () => {
  console.log("Export PDF clicked");

  try {
    const element = document.body;

    const opt = {
      margin:       0.3,
      filename:     "weekly_schedule.pdf",
      html2canvas:  { scale: 2, useCORS: true },
      jsPDF:        { unit: "in", format: "letter", orientation: "landscape" }
    };

    // Create the PDF
    const worker = html2pdf().set(opt).from(element);
    const blob = await worker.outputPdf("blob");

    // Force download
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "weekly_schedule.pdf";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    console.log("PDF download triggered");

  } catch (err) {
    console.error("PDF export failed:", err);
    alert("PDF export failed — check the console.");
  }
});