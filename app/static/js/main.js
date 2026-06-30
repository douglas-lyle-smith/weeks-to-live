const form = document.querySelector("#life-form");
const errorBox = document.querySelector("#error");
const todayText = document.querySelector("#today");
const timeline = document.querySelector("#timeline");
const eventsList = document.querySelector("#events");
const editableEvents = document.querySelector("#editable-events");
const eventForm = document.querySelector("#event-form");
const eventSubmit = document.querySelector("#event-submit");
const cancelEventEdit = document.querySelector("#cancel-event-edit");
const exportEventsCsvButton = document.querySelector("#export-events-csv");
const importEventsCsvButton = document.querySelector("#import-events-csv");
const eventsCsvFile = document.querySelector("#events-csv-file");
const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");

const eventInputs = {
    name: document.querySelector("#event-name"),
    age: document.querySelector("#event-age"),
    date: document.querySelector("#event-date"),
    color: document.querySelector("#event-color"),
};

const stats = {
    deathDate: document.querySelector("#death-date"),
    age: document.querySelector("#age"),
    lived: document.querySelector("#weeks-lived"),
    remaining: document.querySelector("#weeks-remaining"),
    percent: document.querySelector("#percent-used"),
};

const compactQuery = window.matchMedia("(max-width: 700px)");
const state = {
    events: [],
    latestData: null,
    activeEventId: null,
    editingEventId: null,
};

function formatDate(value) {
    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    }).format(new Date(`${value}T00:00:00`));
}

function showError(message) {
    errorBox.textContent = message;
    errorBox.style.display = "block";
}

function clearError() {
    errorBox.textContent = "";
    errorBox.style.display = "none";
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Request failed.");
    }
    return data;
}

function sortEvents(events) {
    return [...events].sort((a, b) => Number(a.age) - Number(b.age) || a.name.localeCompare(b.name));
}

function eventMap(events) {
    const mapped = new Map();
    events.forEach((event) => {
        const bucket = mapped.get(event.week_index) || [];
        bucket.push(event);
        mapped.set(event.week_index, bucket);
    });
    return mapped;
}

function setTimelineOrientation(orientation) {
    timeline.innerHTML = "";
    timeline.className = `timeline ${orientation}`;
}

function eventForWeek(events) {
    if (!events?.length) {
        return null;
    }
    return events.find((event) => event.id === state.activeEventId) || events[0];
}

function createWeek(index, age, weekOfYear, data, eventsByWeek) {
    const week = document.createElement("div");
    if (index >= data.total_weeks) {
        week.className = "week outside";
        return week;
    }

    week.className = `week ${index < data.weeks_lived ? "spent" : ""}`;
    week.title = `Age ${age}, week ${weekOfYear + 1}`;

    const weekEvents = eventsByWeek.get(index) || [];
    const displayEvent = eventForWeek(weekEvents);
    if (displayEvent) {
        const eventIds = weekEvents.map((event) => event.id);
        week.classList.add("event");
        week.classList.toggle("active-event", eventIds.includes(state.activeEventId));
        week.dataset.eventIds = eventIds.join(" ");
        week.style.setProperty("--event-color", displayEvent.color);
        week.title = weekEvents.map((event) => `${event.name}, age ${event.age}`).join("\n");
    }

    return week;
}

function renderHorizontalTimeline(data) {
    setTimelineOrientation("horizontal");
    const eventsByWeek = eventMap(data.events);
    const ageColumns = data.age_columns || Math.ceil(data.total_weeks / 52);
    const fragment = document.createDocumentFragment();

    timeline.style.setProperty("--age-count", ageColumns);

    const corner = document.createElement("div");
    corner.className = "axis-corner";
    corner.textContent = "Age";
    fragment.appendChild(corner);

    for (let age = 0; age < ageColumns; age += 1) {
        const label = document.createElement("div");
        label.className = "age-label";
        label.title = `Age ${age}`;
        if (age % 5 === 0 || age === ageColumns - 1) {
            label.textContent = age;
        }
        fragment.appendChild(label);
    }

    for (let weekOfYear = 0; weekOfYear < 52; weekOfYear += 1) {
        const weekLabel = document.createElement("div");
        weekLabel.className = "week-label";
        weekLabel.title = `Week ${weekOfYear + 1}`;
        if (weekOfYear === 0 || weekOfYear === 51 || weekOfYear % 13 === 12) {
            weekLabel.textContent = weekOfYear + 1;
        }
        fragment.appendChild(weekLabel);

        for (let age = 0; age < ageColumns; age += 1) {
            const index = age * 52 + weekOfYear;
            fragment.appendChild(createWeek(index, age, weekOfYear, data, eventsByWeek));
        }
    }

    timeline.appendChild(fragment);
}

function renderVerticalTimeline(data) {
    setTimelineOrientation("vertical");
    const eventsByWeek = eventMap(data.events);
    const ageColumns = data.age_columns || Math.ceil(data.total_weeks / 52);
    const fragment = document.createDocumentFragment();

    timeline.style.setProperty("--age-count", ageColumns);

    const corner = document.createElement("div");
    corner.className = "axis-corner";
    corner.textContent = "Age";
    fragment.appendChild(corner);

    for (let weekOfYear = 0; weekOfYear < 52; weekOfYear += 1) {
        const label = document.createElement("div");
        label.className = "week-label";
        label.title = `Week ${weekOfYear + 1}`;
        if (weekOfYear === 0 || weekOfYear === 51 || weekOfYear % 13 === 12) {
            label.textContent = weekOfYear + 1;
        }
        fragment.appendChild(label);
    }

    for (let age = 0; age < ageColumns; age += 1) {
        const ageLabel = document.createElement("div");
        ageLabel.className = "age-label";
        ageLabel.textContent = age;
        ageLabel.title = `Age ${age}`;
        fragment.appendChild(ageLabel);

        for (let weekOfYear = 0; weekOfYear < 52; weekOfYear += 1) {
            const index = age * 52 + weekOfYear;
            fragment.appendChild(createWeek(index, age, weekOfYear, data, eventsByWeek));
        }
    }

    timeline.appendChild(fragment);
}

function renderTimeline(data) {
    if (compactQuery.matches) {
        renderVerticalTimeline(data);
        return;
    }

    renderHorizontalTimeline(data);
}

function renderChartEvents(events) {
    eventsList.innerHTML = "";
    sortEvents(events).forEach((event) => {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "event-card";
        card.classList.toggle("active", event.id === state.activeEventId);
        card.style.setProperty("--event-color", event.color);

        const name = document.createElement("strong");
        name.textContent = event.name;
        const details = document.createElement("span");
        details.textContent = `Age ${event.age} - ${event.date}`;
        card.append(name, details);

        card.addEventListener("click", () => highlightEvent(event.id));
        eventsList.appendChild(card);
    });
}

function renderEditableEvents() {
    editableEvents.innerHTML = "";
    sortEvents(state.events).forEach((event) => {
        const row = document.createElement("article");
        row.className = "editable-event";
        row.classList.toggle("editing", event.id === state.editingEventId);
        row.style.setProperty("--event-color", event.color);

        const swatch = document.createElement("span");
        swatch.className = "event-swatch";
        swatch.setAttribute("aria-hidden", "true");

        const summary = document.createElement("div");
        summary.className = "editable-event-summary";
        const name = document.createElement("strong");
        name.textContent = event.name;
        const meta = document.createElement("span");
        meta.textContent = `Age ${event.age} - ${event.date}`;
        summary.append(name, meta);

        const actions = document.createElement("div");
        actions.className = "event-actions";

        const editButton = document.createElement("button");
        editButton.className = "event-edit";
        editButton.type = "button";
        editButton.textContent = "Edit";
        editButton.addEventListener("click", () => beginEditEvent(event.id));

        const deleteButton = document.createElement("button");
        deleteButton.className = "event-delete";
        deleteButton.type = "button";
        deleteButton.textContent = "Delete";
        deleteButton.addEventListener("click", () => deleteEvent(event.id));

        actions.append(editButton, deleteButton);
        row.append(swatch, summary, actions);
        editableEvents.appendChild(row);
    });
}

function renderStats(data) {
    todayText.textContent = formatDate(data.today);
    stats.deathDate.textContent = formatDate(data.death_date);
    stats.age.textContent = `${data.age_years}`;
    stats.lived.textContent = data.weeks_lived.toLocaleString();
    stats.remaining.textContent = data.weeks_remaining.toLocaleString();
    stats.percent.textContent = `${data.percent_used}%`;
}

function highlightEvent(eventId) {
    state.activeEventId = eventId;
    if (!state.latestData) {
        return;
    }
    renderTimeline(state.latestData);
    renderChartEvents(state.latestData.events);

    const target = [...timeline.querySelectorAll(".week.event")]
        .find((week) => (week.dataset.eventIds || "").split(" ").includes(eventId));
    target?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
}

function switchTab(tabName) {
    tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === tabName));
    panels.forEach((panel) => panel.classList.toggle("active", panel.id === `${tabName}-tab`));
}

function resetEventForm() {
    state.editingEventId = null;
    eventForm.classList.remove("editing");
    eventSubmit.textContent = "Add Event";
    cancelEventEdit.hidden = true;
    eventForm.reset();
    eventInputs.color.value = "#0f766e";
}

function beginEditEvent(eventId) {
    const event = state.events.find((item) => item.id === eventId);
    if (!event) {
        return;
    }
    state.editingEventId = event.id;
    eventInputs.name.value = event.name;
    eventInputs.age.value = event.age;
    eventInputs.date.value = event.date;
    eventInputs.color.value = event.color;
    eventSubmit.textContent = "Save Event";
    cancelEventEdit.hidden = false;
    eventForm.classList.add("editing");
    renderEditableEvents();
    eventInputs.name.focus();
}

async function loadSettings() {
    const settings = await requestJson("/api/settings");
    form.birthdate.value = settings.birthdate;
    form.life_expectancy.value = settings.life_expectancy;
}

async function loadEvents() {
    const data = await requestJson("/api/events");
    state.events = data.events;
    renderEditableEvents();
}

async function calculate() {
    clearError();
    const body = {
        birthdate: form.birthdate.value,
        life_expectancy: form.life_expectancy.value,
    };

    const data = await requestJson("/api/calculate", {
        method: "POST",
        body: JSON.stringify(body),
    });

    if (state.activeEventId && !data.events.some((event) => event.id === state.activeEventId)) {
        state.activeEventId = null;
    }
    renderStats(data);
    state.latestData = data;
    renderTimeline(data);
    renderChartEvents(data.events);
}

async function saveEvent(event) {
    event.preventDefault();
    try {
        const payload = {
            name: eventInputs.name.value,
            age: eventInputs.age.value,
            date: eventInputs.date.value,
            color: eventInputs.color.value,
        };
        const editingEventId = state.editingEventId;
        await requestJson(editingEventId ? `/api/events/${editingEventId}` : "/api/events", {
            method: editingEventId ? "PUT" : "POST",
            body: JSON.stringify(payload),
        });
        resetEventForm();
        await loadEvents();
        await calculate();
    } catch (error) {
        showError(error.message);
    }
}

async function deleteEvent(eventId) {
    const event = state.events.find((item) => item.id === eventId);
    if (!event || !window.confirm(`Delete "${event.name}"?`)) {
        return;
    }
    try {
        await requestJson(`/api/events/${eventId}`, { method: "DELETE" });
        if (state.activeEventId === eventId) {
            state.activeEventId = null;
        }
        resetEventForm();
        await loadEvents();
        await calculate();
    } catch (error) {
        showError(error.message);
    }
}

function csvCell(value) {
    const text = String(value ?? "");
    return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

function exportEventsCsvFile() {
    const headers = ["name", "age", "date", "color"];
    const rows = [headers.join(",")];
    sortEvents(state.events).forEach((event) => {
        rows.push(headers.map((header) => csvCell(event[header])).join(","));
    });
    const blob = new Blob([`${rows.join("\r\n")}\r\n`], { type: "text/csv;charset=utf-8" });
    downloadBlob(blob, "weeks-to-live-events.csv");
}

function parseCsvRows(text) {
    const rows = [];
    let row = [];
    let field = "";
    let inQuotes = false;
    const source = text.replace(/^\uFEFF/, "");

    for (let index = 0; index < source.length; index += 1) {
        const char = source[index];
        const next = source[index + 1];
        if (inQuotes) {
            if (char === '"' && next === '"') {
                field += '"';
                index += 1;
            } else if (char === '"') {
                inQuotes = false;
            } else {
                field += char;
            }
        } else if (char === '"') {
            inQuotes = true;
        } else if (char === ",") {
            row.push(field);
            field = "";
        } else if (char === "\n") {
            row.push(field);
            rows.push(row);
            row = [];
            field = "";
        } else if (char !== "\r") {
            field += char;
        }
    }

    if (inQuotes) {
        throw new Error("CSV has an unterminated quoted field.");
    }

    if (field || row.length) {
        row.push(field);
        rows.push(row);
    }

    return rows.filter((cells) => cells.some((cell) => cell.trim()));
}

function normalizeCsvHeader(value) {
    const normalized = String(value || "").trim().toLowerCase().replace(/[^a-z0-9]/g, "");
    if (normalized === "eventname") return "name";
    if (normalized === "eventage" || normalized === "ageyears") return "age";
    if (normalized === "eventdate" || normalized === "datelabel") return "date";
    if (normalized === "eventcolor" || normalized === "colour") return "color";
    return normalized;
}

function eventsFromCsv(text) {
    const rows = parseCsvRows(text);
    if (rows.length < 2) {
        throw new Error("CSV must include headers and at least one event row.");
    }

    const headers = rows[0].map(normalizeCsvHeader);
    const requiredHeaders = ["name", "age", "date", "color"];
    const indexes = Object.fromEntries(requiredHeaders.map((header) => [header, headers.indexOf(header)]));
    const missingHeaders = requiredHeaders.filter((header) => indexes[header] === -1);
    if (missingHeaders.length) {
        throw new Error(`CSV headers must include ${requiredHeaders.join(", ")}. Export CSV to get the expected header row.`);
    }

    return rows.slice(1)
        .map((row, index) => ({
            name: row[indexes.name] || "",
            age: row[indexes.age] || "",
            date: row[indexes.date] || "",
            color: row[indexes.color] || "",
            _row: index + 2,
        }))
        .filter((event) => event.name.trim() || String(event.age).trim() || event.date.trim() || event.color.trim());
}

async function importEventsCsvFile(event) {
    const file = event.target.files?.[0];
    if (!file) {
        return;
    }

    try {
        clearError();
        const importedEvents = eventsFromCsv(await file.text());
        if (!importedEvents.length) {
            throw new Error("CSV did not contain any event rows.");
        }
        await requestJson("/api/events/import", {
            method: "POST",
            body: JSON.stringify({ events: importedEvents }),
        });
        resetEventForm();
        await loadEvents();
        await calculate();
        switchTab("events");
    } catch (error) {
        showError(error.message);
    } finally {
        event.target.value = "";
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await calculate();
    } catch (error) {
        showError(error.message);
    }
});

eventForm.addEventListener("submit", saveEvent);
cancelEventEdit.addEventListener("click", () => {
    resetEventForm();
    renderEditableEvents();
});
tabs.forEach((tab) => tab.addEventListener("click", () => switchTab(tab.dataset.tab)));
exportEventsCsvButton.addEventListener("click", exportEventsCsvFile);
importEventsCsvButton.addEventListener("click", () => {
    eventsCsvFile.value = "";
    eventsCsvFile.click();
});
eventsCsvFile.addEventListener("change", importEventsCsvFile);

function rerenderForViewport() {
    if (state.latestData) {
        renderTimeline(state.latestData);
        renderChartEvents(state.latestData.events);
    }
}

if (typeof compactQuery.addEventListener === "function") {
    compactQuery.addEventListener("change", rerenderForViewport);
} else {
    compactQuery.addListener(rerenderForViewport);
}

async function init() {
    try {
        await loadSettings();
        await loadEvents();
        await calculate();
    } catch (error) {
        showError(error.message);
    }
}

init();
