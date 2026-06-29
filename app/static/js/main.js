const form = document.querySelector("#life-form");
const errorBox = document.querySelector("#error");
const todayText = document.querySelector("#today");
const timeline = document.querySelector("#timeline");
const eventsList = document.querySelector("#events");
const stats = {
    deathDate: document.querySelector("#death-date"),
    age: document.querySelector("#age"),
    lived: document.querySelector("#weeks-lived"),
    remaining: document.querySelector("#weeks-remaining"),
    percent: document.querySelector("#percent-used"),
};
const compactQuery = window.matchMedia("(max-width: 700px)");
let latestData = null;

function formatDate(value) {
    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    }).format(new Date(`${value}T00:00:00`));
}

function eventMap(events) {
    const mapped = new Map();
    events.forEach((event) => mapped.set(event.week_index, event));
    return mapped;
}

function setTimelineOrientation(orientation) {
    timeline.innerHTML = "";
    timeline.className = `timeline ${orientation}`;
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
            const week = document.createElement("div");

            if (index >= data.total_weeks) {
                week.className = "week outside";
                fragment.appendChild(week);
                continue;
            }

            week.className = `week ${index < data.weeks_lived ? "spent" : ""}`;
            week.title = `Age ${age}, week ${weekOfYear + 1}`;

            const event = eventsByWeek.get(index);
            if (event) {
                week.classList.add("event");
                week.style.setProperty("--event-color", event.color);
                week.title = `${event.name}, age ${event.age}`;
            }

            fragment.appendChild(week);
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
            const week = document.createElement("div");

            if (index >= data.total_weeks) {
                week.className = "week outside";
                fragment.appendChild(week);
                continue;
            }

            week.className = `week ${index < data.weeks_lived ? "spent" : ""}`;
            week.title = `Age ${age}, week ${weekOfYear + 1}`;

            const event = eventsByWeek.get(index);
            if (event) {
                week.classList.add("event");
                week.style.setProperty("--event-color", event.color);
                week.title = `${event.name}, age ${event.age}`;
            }

            fragment.appendChild(week);
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

function renderEvents(events) {
    eventsList.innerHTML = "";
    events.forEach((event) => {
        const card = document.createElement("article");
        card.className = "event-card";
        card.innerHTML = `
            <strong>${event.name}</strong>
            <span>Age ${event.age} - ${event.date}</span>
        `;
        card.style.borderLeft = `5px solid ${event.color}`;
        eventsList.appendChild(card);
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

async function calculate() {
    errorBox.style.display = "none";
    const body = {
        birthdate: form.birthdate.value,
        life_expectancy: form.life_expectancy.value,
    };

    const response = await fetch("/api/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Unable to calculate life table.");
    }

    renderStats(data);
    latestData = data;
    renderTimeline(data);
    renderEvents(data.events);
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await calculate();
    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.style.display = "block";
    }
});

function rerenderForViewport() {
    if (latestData) {
        renderTimeline(latestData);
    }
}

if (typeof compactQuery.addEventListener === "function") {
    compactQuery.addEventListener("change", rerenderForViewport);
} else {
    compactQuery.addListener(rerenderForViewport);
}

calculate();
