from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta
from math import ceil
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
STATIC_DIR = Path(__file__).parent / "static"

DEFAULT_EVENTS = [
    {
        "id": "jesus-crucified",
        "name": "Jesus is Crucified",
        "age": 33,
        "color": "#dc2626",
        "date": "AD 30-33",
    },
    {
        "id": "mlk-i-have-a-dream",
        "name": 'MLK "I Have a Dream"',
        "age": 34,
        "color": "#2563eb",
        "date": "August 28, 1963",
    },
    {
        "id": "rosa-parks-bus-boycott",
        "name": "Rosa Parks Bus Boycott",
        "age": 42,
        "color": "#16a34a",
        "date": "December 1, 1955",
    },
    {
        "id": "washington-crossing-the-delaware",
        "name": "George Washington Crossing the Delaware",
        "age": 44,
        "color": "#0891b2",
        "date": "December 25, 1776",
    },
    {
        "id": "galileo-jupiter-moons",
        "name": "Galileo Discovers Jupiter's Moons",
        "age": 45,
        "color": "#7f1d1d",
        "date": "1610",
    },
    {
        "id": "lincoln-emancipation-proclamation",
        "name": "Lincoln Emancipation Proclamation",
        "age": 54,
        "color": "#111827",
        "date": "January 1, 1863",
    },
    {
        "id": "gandhi-salt-march",
        "name": "Gandhi Salt March",
        "age": 60,
        "color": "#a16207",
        "date": "March 12, 1930",
    },
    {
        "id": "churchill-never-surrender",
        "name": 'Churchill "We Shall Never Surrender" Speech',
        "age": 65,
        "color": "#c026d3",
        "date": "June 4, 1940",
    },
    {
        "id": "mother-teresa-nobel-peace-prize",
        "name": "Mother Teresa Receives Nobel Peace Prize",
        "age": 69,
        "color": "#374151",
        "date": "December 10, 1979",
    },
]

DAYS_PER_YEAR = 365.2425
MAX_LIFE_EXPECTANCY = 130
MAX_EVENT_NAME_LENGTH = 140
MAX_EVENT_DATE_LABEL_LENGTH = 80
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
DEFAULT_SETTINGS = {
    "birthdate": "1980-09-08",
    "life_expectancy": 78.6,
}


def data_dir() -> Path:
    configured = os.environ.get("WEEKS_TO_LIVE_DATA_DIR")
    path = Path(configured) if configured else Path.cwd() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def events_path() -> Path:
    return data_dir() / "events.json"


def settings_path() -> Path:
    return data_dir() / "settings.json"


def normalize_event_id(value: str | None = None) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", (value or "").lower()).strip("-")
    return cleaned or uuid4().hex


def sorted_events(events: list[dict]) -> list[dict]:
    return sorted(events, key=lambda item: (float(item["age"]), item["name"].lower()))


def seed_events() -> list[dict]:
    return sorted_events([dict(event) for event in DEFAULT_EVENTS])


def load_events() -> list[dict]:
    path = events_path()
    if not path.exists():
        events = seed_events()
        write_events(events)
        return events

    with path.open("r", encoding="utf-8") as handle:
        raw_events = json.load(handle)

    events = []
    seen_ids = set()
    for event in raw_events:
        normalized = validate_event(event, event_id=event.get("id"))
        while normalized["id"] in seen_ids:
            normalized["id"] = uuid4().hex
        seen_ids.add(normalized["id"])
        events.append(normalized)
    return sorted_events(events)


def write_events(events: list[dict]) -> None:
    path = events_path()
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(sorted_events(events), handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp_path.replace(path)


def load_settings() -> dict:
    path = settings_path()
    if not path.exists():
        write_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    with path.open("r", encoding="utf-8") as handle:
        raw_settings = json.load(handle)

    return validate_settings(raw_settings)


def write_settings(settings: dict) -> None:
    path = settings_path()
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp_path.replace(path)


def clean_text(value: str | None, field_name: str, max_length: int) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    if len(text) > max_length:
        raise ValueError(f"{field_name} cannot exceed {max_length} characters.")
    return text


def parse_event_age(value: str | int | float) -> float:
    try:
        age = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Event age must be a number.") from exc

    if age < 0:
        raise ValueError("Event age cannot be negative.")
    if age > MAX_LIFE_EXPECTANCY:
        raise ValueError(f"Event age cannot exceed {MAX_LIFE_EXPECTANCY} years.")
    return round(age, 2)


def validate_event(payload: dict, event_id: str | None = None) -> dict:
    name = clean_text(payload.get("name"), "Event name", MAX_EVENT_NAME_LENGTH)
    date_label = clean_text(payload.get("date"), "Event date label", MAX_EVENT_DATE_LABEL_LENGTH)
    color = clean_text(payload.get("color"), "Event color", 7)
    if not HEX_COLOR_RE.fullmatch(color):
        raise ValueError("Event color must be a 6-digit hex color.")

    return {
        "id": normalize_event_id(event_id or payload.get("id") or name),
        "name": name,
        "age": parse_event_age(payload.get("age")),
        "color": color.lower(),
        "date": date_label,
    }


def validate_settings(payload: dict) -> dict:
    birthdate = parse_birthdate(payload.get("birthdate", DEFAULT_SETTINGS["birthdate"])).isoformat()
    life_expectancy = parse_life_expectancy(payload.get("life_expectancy", DEFAULT_SETTINGS["life_expectancy"]))
    return {
        "birthdate": birthdate,
        "life_expectancy": round(life_expectancy, 2),
    }


def parse_birthdate(value: str) -> date:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Birthdate must use YYYY-MM-DD.") from exc

    if parsed > date.today():
        raise ValueError("Birthdate cannot be in the future.")
    return parsed


def parse_life_expectancy(value: str | int | float) -> float:
    try:
        years = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Life expectancy must be a number.") from exc

    if years <= 0:
        raise ValueError("Life expectancy must be greater than zero.")
    if years > MAX_LIFE_EXPECTANCY:
        raise ValueError(f"Life expectancy cannot exceed {MAX_LIFE_EXPECTANCY} years.")
    return years


def estimate_death_date(birthdate: date, life_expectancy: float) -> date:
    whole_years = int(life_expectancy)
    fractional_year = life_expectancy - whole_years

    try:
        estimated = birthdate.replace(year=birthdate.year + whole_years)
    except ValueError:
        estimated = birthdate.replace(
            year=birthdate.year + whole_years,
            month=2,
            day=28,
        )

    if fractional_year:
        estimated += timedelta(days=round(fractional_year * DAYS_PER_YEAR))

    return estimated


def calculate_life_stats(
    birthdate_value: str,
    life_expectancy_value: str | int | float,
    events: list[dict] | None = None,
    as_of: date | None = None,
) -> dict:
    birthdate = parse_birthdate(birthdate_value)
    life_expectancy = parse_life_expectancy(life_expectancy_value)
    today = as_of or date.today()
    death_date = estimate_death_date(birthdate, life_expectancy)

    lived_days = max(0, (today - birthdate).days)
    total_days = max(1, (death_date - birthdate).days)
    total_weeks = max(1, ceil(total_days / 7))
    age_columns = max(1, ceil(total_weeks / 52))
    weeks_lived = min(total_weeks, lived_days // 7)
    weeks_remaining = max(0, total_weeks - weeks_lived)
    age_years = lived_days / DAYS_PER_YEAR

    visible_events = []
    source_events = events if events is not None else seed_events()
    for event in sorted_events(source_events):
        if event["age"] <= life_expectancy:
            visible_events.append(
                {
                    **event,
                    "week_index": min(total_weeks - 1, round(float(event["age"]) * 52)),
                }
            )

    return {
        "birthdate": birthdate.isoformat(),
        "life_expectancy": round(life_expectancy, 2),
        "today": today.isoformat(),
        "death_date": death_date.isoformat(),
        "age_years": round(age_years, 1),
        "total_weeks": total_weeks,
        "age_columns": age_columns,
        "weeks_lived": weeks_lived,
        "weeks_remaining": weeks_remaining,
        "percent_used": round((weeks_lived / total_weeks) * 100, 1),
        "events": visible_events,
    }


def asset_version() -> str:
    paths = [
        STATIC_DIR / "css" / "style.css",
        STATIC_DIR / "js" / "main.js",
    ]
    return str(int(max(path.stat().st_mtime for path in paths)))


@app.route("/")
def index():
    return render_template("index.html", asset_version=asset_version())


@app.route("/api/calculate", methods=["POST"])
def calculate():
    payload = request.get_json(silent=True) or {}

    try:
        settings = validate_settings(payload)
        stats = calculate_life_stats(
            settings["birthdate"],
            settings["life_expectancy"],
            events=load_events(),
        )
        write_settings(settings)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(stats)


@app.route("/api/settings", methods=["GET"])
def get_settings():
    try:
        settings = load_settings()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(settings)


@app.route("/api/events", methods=["GET"])
def list_events():
    return jsonify({"events": load_events()})


@app.route("/api/events", methods=["POST"])
def create_event():
    payload = request.get_json(silent=True) or {}
    try:
        event = validate_event(payload, event_id=uuid4().hex)
        events = load_events()
        events.append(event)
        write_events(events)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(event), 201


@app.route("/api/events/<event_id>", methods=["PUT"])
def update_event(event_id: str):
    events = load_events()
    event_index = next((index for index, event in enumerate(events) if event["id"] == event_id), None)
    if event_index is None:
        return jsonify({"error": "Event not found."}), 404

    payload = request.get_json(silent=True) or {}
    try:
        events[event_index] = validate_event(payload, event_id=event_id)
        write_events(events)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(events[event_index])


@app.route("/api/events/<event_id>", methods=["DELETE"])
def delete_event(event_id: str):
    events = load_events()
    remaining = [event for event in events if event["id"] != event_id]
    if len(remaining) == len(events):
        return jsonify({"error": "Event not found."}), 404
    write_events(remaining)
    return jsonify({"deleted": event_id})


@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "service": "weeks-to-live"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
