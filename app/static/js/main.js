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

function renderTimeline(data) {
    timeline.innerHTML = "";
    const eventsByWeek = eventMap(data.events);

    for (let index = 0; index < data.total_weeks; index += 1) {
        if (index % 52 === 0) {
            const label = document.createElement("div");
            label.className = "year-label";
            label.textContent = Math.floor(index / 52);
            timeline.appendChild(label);
        }

        const week = document.createElement("div");
        week.className = `week ${index < data.weeks_lived ? "spent" : ""}`;

        const event = eventsByWeek.get(index);
        if (event) {
            week.classList.add("event");
            week.style.setProperty("--event-color", event.color);
            week.title = `${event.name}, age ${event.age}`;
        }

        timeline.appendChild(week);
    }
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

calculate();
