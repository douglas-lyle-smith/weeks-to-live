const form = document.querySelector("#life-form");
const errorBox = document.querySelector("#error");
const todayText = document.querySelector("#today");
const timeline = document.querySelector("#timeline");
const eventsList = document.querySelector("#events");
const personalEventsCards = document.querySelector("#personal-events-cards");
const editableEvents = document.querySelector("#editable-events");
const editablePersonalEvents = document.querySelector("#editable-personal-events");
const eventForm = document.querySelector("#event-form");
const personalEventForm = document.querySelector("#personal-event-form");
const eventSubmit = document.querySelector("#event-submit");
const personalSubmit = document.querySelector("#personal-submit");
const cancelEventEdit = document.querySelector("#cancel-event-edit");
const cancelPersonalEdit = document.querySelector("#cancel-personal-edit");
const exportEventsCsvButton = document.querySelector("#export-events-csv");
const importEventsCsvButton = document.querySelector("#import-events-csv");
const eventsCsvFile = document.querySelector("#events-csv-file");
const exportPersonalCsvButton = document.querySelector("#export-personal-csv");
const importPersonalCsvButton = document.querySelector("#import-personal-csv");
const personalCsvFile = document.querySelector("#personal-csv-file");
const showEventsToggle = document.querySelector("#show-events-toggle");
const showPersonalEventsToggle = document.querySelector("#show-personal-events-toggle");
const settingsForm = document.querySelector("#settings-form");
const settingsSubmit = document.querySelector("#settings-submit");
const settingsReset = document.querySelector("#settings-reset");
const settingsError = document.querySelector("#settings-error");
const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");
const EVENTS_VISIBILITY_STORAGE_KEY = "weeksToLiveShowEvents";
const PERSONAL_EVENTS_VISIBILITY_STORAGE_KEY = "weeksToLiveShowPersonalEvents";

const DEFAULT_COLORS = {
    lived: "#334155",
    remaining: "#f6d365",
    personal: "#f97316",
    historical: "#ef4444",
};

// Settings color key -> CSS custom property that paints that dot type.
const COLOR_CSS_VARS = {
    lived: "--spent",
    remaining: "--future",
    personal: "--personal",
    historical: "--event",
};

const colorInputs = {
    lived: document.querySelector("#color-lived"),
    remaining: document.querySelector("#color-remaining"),
    personal: document.querySelector("#color-personal"),
    historical: document.querySelector("#color-historical"),
};

const eventInputs = {
    name: document.querySelector("#event-name"),
    age: document.querySelector("#event-age"),
    date: document.querySelector("#event-date"),
    color: document.querySelector("#event-color"),
};

const personalInputs = {
    name: document.querySelector("#personal-name"),
    date: document.querySelector("#personal-date"),
    end_date: document.querySelector("#personal-end-date"),
    details: document.querySelector("#personal-details"),
    color: document.querySelector("#personal-color"),
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
    personalEvents: [],
    latestData: null,
    activeEventId: null,
    activePersonalId: null,
    editingEventId: null,
    editingPersonalId: null,
    showEvents: loadEventsVisibility(),
    showPersonalEvents: loadPersonalEventsVisibility(),
    colors: { ...DEFAULT_COLORS },
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

function loadEventsVisibility() {
    try {
        return window.localStorage.getItem(EVENTS_VISIBILITY_STORAGE_KEY) !== "false";
    } catch (error) {
        return true;
    }
}

function saveEventsVisibility() {
    try {
        window.localStorage.setItem(EVENTS_VISIBILITY_STORAGE_KEY, state.showEvents ? "true" : "false");
    } catch (error) {
        // Browsers may block localStorage in private or locked-down contexts.
    }
}

function loadPersonalEventsVisibility() {
    try {
        return window.localStorage.getItem(PERSONAL_EVENTS_VISIBILITY_STORAGE_KEY) !== "false";
    } catch (error) {
        return true;
    }
}

function savePersonalEventsVisibility() {
    try {
        window.localStorage.setItem(
            PERSONAL_EVENTS_VISIBILITY_STORAGE_KEY,
            state.showPersonalEvents ? "true" : "false",
        );
    } catch (error) {
        // Browsers may block localStorage in private or locked-down contexts.
    }
}

function visibleChartEvents(data) {
    return state.showEvents ? data.events : [];
}

function visibleChartPersonalEvents(data) {
    return state.showPersonalEvents ? data.personal_events || [] : [];
}

function formatDateRange(startValue, endValue) {
    const start = formatDate(startValue);
    if (!endValue || endValue === startValue) {
        return start;
    }
    return `${start} – ${formatDate(endValue)}`;
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

function personalEventMap(events) {
    const mapped = new Map();
    events.forEach((event) => {
        const start = Number(event.week_start);
        const end = Number(event.week_end);
        for (let week = start; week <= end; week += 1) {
            const bucket = mapped.get(week) || [];
            bucket.push(event);
            mapped.set(week, bucket);
        }
    });
    return mapped;
}

function personalEventForWeek(events) {
    if (!events?.length) {
        return null;
    }
    return events.find((event) => event.id === state.activePersonalId) || events[0];
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

function createWeek(index, age, weekOfYear, data, eventsByWeek, personalByWeek) {
    const week = document.createElement("div");
    if (index >= data.total_weeks) {
        week.className = "week outside";
        return week;
    }

    week.className = `week ${index < data.weeks_lived ? "spent" : ""}`;
    week.title = `Age ${age}, week ${weekOfYear + 1}`;

    const personalEvents = personalByWeek.get(index) || [];
    const displayPersonal = personalEventForWeek(personalEvents);
    if (displayPersonal) {
        const personalIds = personalEvents.map((event) => event.id);
        week.classList.add("personal-event");
        week.classList.toggle("active-personal", personalIds.includes(state.activePersonalId));
        week.dataset.personalIds = personalIds.join(" ");
        week.style.setProperty("--personal-color", displayPersonal.color);
        week.title = personalEvents
            .map((event) => `${event.name} (${event.date}${event.end_date && event.end_date !== event.date ? ` – ${event.end_date}` : ""})`)
            .join("\n");
    }

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

    if (displayPersonal || displayEvent) {
        week.classList.add("clickable");
        week.addEventListener("click", () => {
            if (displayPersonal) {
                highlightPersonalEvent(displayPersonal.id);
            } else {
                highlightEvent(displayEvent.id);
            }
        });
    }

    return week;
}

function renderHorizontalTimeline(data) {
    setTimelineOrientation("horizontal");
    const eventsByWeek = eventMap(visibleChartEvents(data));
    const personalByWeek = personalEventMap(visibleChartPersonalEvents(data));
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
            fragment.appendChild(createWeek(index, age, weekOfYear, data, eventsByWeek, personalByWeek));
        }
    }

    timeline.appendChild(fragment);
}

function renderVerticalTimeline(data) {
    setTimelineOrientation("vertical");
    const eventsByWeek = eventMap(visibleChartEvents(data));
    const personalByWeek = personalEventMap(visibleChartPersonalEvents(data));
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
            fragment.appendChild(createWeek(index, age, weekOfYear, data, eventsByWeek, personalByWeek));
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
    eventsList.hidden = !state.showEvents;
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

function sortPersonalEvents(events) {
    return [...events].sort(
        (a, b) =>
            String(a.date).localeCompare(String(b.date)) ||
            String(a.end_date).localeCompare(String(b.end_date)) ||
            a.name.localeCompare(b.name),
    );
}

function renderPersonalCards(events) {
    personalEventsCards.innerHTML = "";
    personalEventsCards.hidden = !state.showPersonalEvents || !events.length;
    sortPersonalEvents(events).forEach((event) => {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "event-card personal-card";
        card.classList.toggle("active", event.id === state.activePersonalId);
        card.style.setProperty("--event-color", event.color);

        const tag = document.createElement("span");
        tag.className = "personal-tag";
        tag.textContent = "Personal Event";

        const name = document.createElement("strong");
        name.textContent = event.name;

        const when = document.createElement("span");
        when.className = "personal-when";
        when.textContent = formatDateRange(event.date, event.end_date);

        card.append(tag, name, when);

        if (event.details) {
            const details = document.createElement("span");
            details.className = "personal-details";
            details.textContent = event.details;
            card.append(details);
        }

        card.addEventListener("click", () => highlightPersonalEvent(event.id));
        personalEventsCards.appendChild(card);
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

function renderEditablePersonalEvents() {
    editablePersonalEvents.innerHTML = "";
    if (!state.personalEvents.length) {
        const empty = document.createElement("p");
        empty.className = "empty-hint";
        empty.textContent = "No personal events yet. Add one above or import a CSV.";
        editablePersonalEvents.appendChild(empty);
        return;
    }

    sortPersonalEvents(state.personalEvents).forEach((event) => {
        const row = document.createElement("article");
        row.className = "editable-event personal-editable";
        row.classList.toggle("editing", event.id === state.editingPersonalId);
        row.classList.toggle("disabled", event.enabled === false);
        row.style.setProperty("--event-color", event.color);

        const swatch = document.createElement("span");
        swatch.className = "event-swatch";
        swatch.setAttribute("aria-hidden", "true");

        const summary = document.createElement("div");
        summary.className = "editable-event-summary";
        const name = document.createElement("strong");
        name.textContent = event.name;
        const meta = document.createElement("span");
        meta.textContent = formatDateRange(event.date, event.end_date);
        summary.append(name, meta);
        if (event.details) {
            const details = document.createElement("span");
            details.className = "editable-details";
            details.textContent = event.details;
            summary.append(details);
        }

        const actions = document.createElement("div");
        actions.className = "event-actions";

        const toggle = document.createElement("label");
        toggle.className = "record-toggle";
        toggle.title = event.enabled === false ? "Hidden on chart" : "Shown on chart";
        const toggleInput = document.createElement("input");
        toggleInput.type = "checkbox";
        toggleInput.setAttribute("role", "switch");
        toggleInput.checked = event.enabled !== false;
        toggleInput.addEventListener("change", () => togglePersonalEvent(event.id, toggleInput.checked));
        const toggleSlider = document.createElement("span");
        toggleSlider.className = "switch-slider";
        toggleSlider.setAttribute("aria-hidden", "true");
        toggle.append(toggleInput, toggleSlider);

        const editButton = document.createElement("button");
        editButton.className = "event-edit";
        editButton.type = "button";
        editButton.textContent = "Edit";
        editButton.addEventListener("click", () => beginEditPersonalEvent(event.id));

        const deleteButton = document.createElement("button");
        deleteButton.className = "event-delete";
        deleteButton.type = "button";
        deleteButton.textContent = "Delete";
        deleteButton.addEventListener("click", () => deletePersonalEvent(event.id));

        actions.append(toggle, editButton, deleteButton);
        row.append(swatch, summary, actions);
        editablePersonalEvents.appendChild(row);
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

function rerenderChart() {
    if (!state.latestData) {
        return;
    }
    renderTimeline(state.latestData);
    renderChartEvents(visibleChartEvents(state.latestData));
    renderPersonalCards(visibleChartPersonalEvents(state.latestData));
}

function highlightEvent(eventId) {
    state.activeEventId = eventId;
    state.activePersonalId = null;
    rerenderChart();

    const target = [...timeline.querySelectorAll(".week.event")]
        .find((week) => (week.dataset.eventIds || "").split(" ").includes(eventId));
    target?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
}

function highlightPersonalEvent(eventId) {
    state.activePersonalId = eventId;
    state.activeEventId = null;
    rerenderChart();

    const target = [...timeline.querySelectorAll(".week.personal-event")]
        .find((week) => (week.dataset.personalIds || "").split(" ").includes(eventId));
    target?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
}

function setEventsVisibility(showEvents) {
    state.showEvents = showEvents;
    showEventsToggle.checked = showEvents;
    saveEventsVisibility();
    rerenderChart();
}

function setPersonalEventsVisibility(showPersonalEvents) {
    state.showPersonalEvents = showPersonalEvents;
    showPersonalEventsToggle.checked = showPersonalEvents;
    savePersonalEventsVisibility();
    rerenderChart();
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

function resetPersonalEventForm() {
    state.editingPersonalId = null;
    personalEventForm.classList.remove("editing");
    personalSubmit.textContent = "Add Personal Event";
    cancelPersonalEdit.hidden = true;
    personalEventForm.reset();
    personalInputs.color.value = state.colors.personal;
}

function beginEditPersonalEvent(eventId) {
    const event = state.personalEvents.find((item) => item.id === eventId);
    if (!event) {
        return;
    }
    state.editingPersonalId = event.id;
    personalInputs.name.value = event.name;
    personalInputs.date.value = event.date;
    personalInputs.end_date.value = event.end_date && event.end_date !== event.date ? event.end_date : "";
    personalInputs.details.value = event.details || "";
    personalInputs.color.value = event.color;
    personalSubmit.textContent = "Save Personal Event";
    cancelPersonalEdit.hidden = false;
    personalEventForm.classList.add("editing");
    renderEditablePersonalEvents();
    personalInputs.name.focus();
}

function applyColors(colors) {
    Object.entries(COLOR_CSS_VARS).forEach(([key, cssVar]) => {
        const value = colors?.[key];
        if (value) {
            document.documentElement.style.setProperty(cssVar, value);
        }
    });
}

function populateColorInputs(colors) {
    Object.entries(colorInputs).forEach(([key, input]) => {
        if (input && colors?.[key]) {
            input.value = colors[key];
        }
    });
}

function useColors(colors) {
    state.colors = { ...DEFAULT_COLORS, ...(colors || {}) };
    applyColors(state.colors);
    populateColorInputs(state.colors);
    if (!state.editingPersonalId) {
        personalInputs.color.value = state.colors.personal;
    }
}

function showSettingsError(message) {
    settingsError.textContent = message;
    settingsError.style.display = "block";
}

function clearSettingsError() {
    settingsError.textContent = "";
    settingsError.style.display = "none";
}

async function saveColors(colors) {
    clearSettingsError();
    const settings = await requestJson("/api/settings", {
        method: "POST",
        body: JSON.stringify({ colors }),
    });
    useColors(settings.colors);
}

async function loadSettings() {
    const settings = await requestJson("/api/settings");
    form.birthdate.value = settings.birthdate;
    form.life_expectancy.value = settings.life_expectancy;
    useColors(settings.colors);
}

async function loadEvents() {
    const data = await requestJson("/api/events");
    state.events = data.events;
    renderEditableEvents();
}

async function loadPersonalEvents() {
    const data = await requestJson("/api/personal-events");
    state.personalEvents = data.personal_events || [];
    renderEditablePersonalEvents();
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
    const personalEvents = data.personal_events || [];
    if (state.activePersonalId && !personalEvents.some((event) => event.id === state.activePersonalId)) {
        state.activePersonalId = null;
    }
    renderStats(data);
    state.latestData = data;
    renderTimeline(data);
    renderChartEvents(visibleChartEvents(data));
    renderPersonalCards(visibleChartPersonalEvents(data));
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

async function savePersonalEvent(event) {
    event.preventDefault();
    try {
        const payload = {
            name: personalInputs.name.value,
            date: personalInputs.date.value,
            end_date: personalInputs.end_date.value,
            details: personalInputs.details.value,
            color: personalInputs.color.value,
        };
        const editingPersonalId = state.editingPersonalId;
        await requestJson(editingPersonalId ? `/api/personal-events/${editingPersonalId}` : "/api/personal-events", {
            method: editingPersonalId ? "PUT" : "POST",
            body: JSON.stringify(payload),
        });
        resetPersonalEventForm();
        await loadPersonalEvents();
        await calculate();
    } catch (error) {
        showError(error.message);
    }
}

async function deletePersonalEvent(eventId) {
    const event = state.personalEvents.find((item) => item.id === eventId);
    if (!event || !window.confirm(`Delete "${event.name}"?`)) {
        return;
    }
    try {
        await requestJson(`/api/personal-events/${eventId}`, { method: "DELETE" });
        if (state.activePersonalId === eventId) {
            state.activePersonalId = null;
        }
        if (state.editingPersonalId === eventId) {
            resetPersonalEventForm();
        }
        await loadPersonalEvents();
        await calculate();
    } catch (error) {
        showError(error.message);
    }
}

async function togglePersonalEvent(eventId, enabled) {
    try {
        clearError();
        await requestJson(`/api/personal-events/${eventId}/toggle`, {
            method: "POST",
            body: JSON.stringify({ enabled }),
        });
        await loadPersonalEvents();
        await calculate();
    } catch (error) {
        showError(error.message);
        await loadPersonalEvents();
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

function exportPersonalCsvFile() {
    const headers = ["date", "end_date", "name", "timelines", "details"];
    const rows = [headers.join(",")];
    sortPersonalEvents(state.personalEvents).forEach((event) => {
        rows.push(headers.map((header) => csvCell(event[header])).join(","));
    });
    const blob = new Blob([`${rows.join("\r\n")}\r\n`], { type: "text/csv;charset=utf-8" });
    downloadBlob(blob, "weeks-to-live-personal-events.csv");
}

function normalizePersonalCsvHeader(value) {
    const normalized = String(value || "").trim().toLowerCase().replace(/[^a-z0-9]/g, "");
    if (normalized === "date" || normalized === "startdate" || normalized === "start") return "date";
    if (normalized === "enddate" || normalized === "end" || normalized === "finish") return "end_date";
    if (normalized === "name" || normalized === "eventname" || normalized === "event" || normalized === "title") return "name";
    if (normalized === "timelines" || normalized === "timeline") return "timelines";
    if (normalized === "details" || normalized === "detail" || normalized === "description" || normalized === "notes") return "details";
    return normalized;
}

function personalEventsFromCsv(text) {
    const rows = parseCsvRows(text);
    if (rows.length < 2) {
        throw new Error("CSV must include headers and at least one event row.");
    }

    const headers = rows[0].map(normalizePersonalCsvHeader);
    const requiredHeaders = ["date", "name"];
    const optionalHeaders = ["end_date", "timelines", "details"];
    const allHeaders = [...requiredHeaders, ...optionalHeaders];
    const indexes = Object.fromEntries(allHeaders.map((header) => [header, headers.indexOf(header)]));
    const missingHeaders = requiredHeaders.filter((header) => indexes[header] === -1);
    if (missingHeaders.length) {
        throw new Error(
            "CSV headers must include date and name (optional: end_date, timelines, details). Export CSV to get the expected header row.",
        );
    }

    const cell = (row, header) => (indexes[header] === -1 ? "" : row[indexes[header]] || "");

    return rows.slice(1)
        .map((row, index) => ({
            date: cell(row, "date").trim(),
            end_date: cell(row, "end_date").trim(),
            name: cell(row, "name"),
            timelines: cell(row, "timelines"),
            details: cell(row, "details"),
            _row: index + 2,
        }))
        .filter((event) => event.name.trim() || event.date.trim() || event.details.trim());
}

async function importPersonalCsvFile(event) {
    const file = event.target.files?.[0];
    if (!file) {
        return;
    }

    try {
        clearError();
        const importedEvents = personalEventsFromCsv(await file.text());
        if (!importedEvents.length) {
            throw new Error("CSV did not contain any personal event rows.");
        }
        await requestJson("/api/personal-events/import", {
            method: "POST",
            body: JSON.stringify({ events: importedEvents }),
        });
        resetPersonalEventForm();
        await loadPersonalEvents();
        await calculate();
        switchTab("personal");
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
personalEventForm.addEventListener("submit", savePersonalEvent);
cancelEventEdit.addEventListener("click", () => {
    resetEventForm();
    renderEditableEvents();
});
cancelPersonalEdit.addEventListener("click", () => {
    resetPersonalEventForm();
    renderEditablePersonalEvents();
});
tabs.forEach((tab) => tab.addEventListener("click", () => switchTab(tab.dataset.tab)));
exportEventsCsvButton.addEventListener("click", exportEventsCsvFile);
importEventsCsvButton.addEventListener("click", () => {
    eventsCsvFile.value = "";
    eventsCsvFile.click();
});
eventsCsvFile.addEventListener("change", importEventsCsvFile);
exportPersonalCsvButton.addEventListener("click", exportPersonalCsvFile);
importPersonalCsvButton.addEventListener("click", () => {
    personalCsvFile.value = "";
    personalCsvFile.click();
});
personalCsvFile.addEventListener("change", importPersonalCsvFile);
showEventsToggle.addEventListener("change", () => setEventsVisibility(showEventsToggle.checked));
showEventsToggle.checked = state.showEvents;
showPersonalEventsToggle.addEventListener("change", () => setPersonalEventsVisibility(showPersonalEventsToggle.checked));
showPersonalEventsToggle.checked = state.showPersonalEvents;

settingsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await saveColors({
            lived: colorInputs.lived.value,
            remaining: colorInputs.remaining.value,
            personal: colorInputs.personal.value,
            historical: colorInputs.historical.value,
        });
    } catch (error) {
        showSettingsError(error.message);
    }
});
// Live preview as the user picks colors, without persisting until Save.
// Dots read the CSS custom properties directly, so setting them repaints the
// chart with no re-render.
Object.entries(colorInputs).forEach(([key, input]) => {
    input.addEventListener("input", () => {
        document.documentElement.style.setProperty(COLOR_CSS_VARS[key], input.value);
    });
});
settingsReset.addEventListener("click", async () => {
    populateColorInputs(DEFAULT_COLORS);
    try {
        await saveColors({ ...DEFAULT_COLORS });
    } catch (error) {
        showSettingsError(error.message);
    }
});

function rerenderForViewport() {
    rerenderChart();
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
        await loadPersonalEvents();
        await calculate();
    } catch (error) {
        showError(error.message);
    }
}

init();
