from __future__ import annotations

from datetime import date, datetime, timedelta
from math import ceil

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

EVENTS = [
    {
        "name": "Jesus is Crucified",
        "age": 33,
        "color": "#dc2626",
        "date": "AD 30-33",
    },
    {
        "name": 'MLK "I Have a Dream"',
        "age": 34,
        "color": "#2563eb",
        "date": "August 28, 1963",
    },
    {
        "name": "Rosa Parks Bus Boycott",
        "age": 42,
        "color": "#16a34a",
        "date": "December 1, 1955",
    },
    {
        "name": "George Washington Crossing the Delaware",
        "age": 44,
        "color": "#0891b2",
        "date": "December 25, 1776",
    },
    {
        "name": "Galileo Discovers Jupiter's Moons",
        "age": 45,
        "color": "#7f1d1d",
        "date": "1610",
    },
    {
        "name": "Lincoln Emancipation Proclamation",
        "age": 54,
        "color": "#111827",
        "date": "January 1, 1863",
    },
    {
        "name": "Gandhi Salt March",
        "age": 60,
        "color": "#a16207",
        "date": "March 12, 1930",
    },
    {
        "name": 'Churchill "We Shall Never Surrender" Speech',
        "age": 65,
        "color": "#c026d3",
        "date": "June 4, 1940",
    },
    {
        "name": "Mother Teresa Receives Nobel Peace Prize",
        "age": 69,
        "color": "#374151",
        "date": "December 10, 1979",
    },
]

DAYS_PER_YEAR = 365.2425
MAX_LIFE_EXPECTANCY = 130


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
    as_of: date | None = None,
) -> dict:
    birthdate = parse_birthdate(birthdate_value)
    life_expectancy = parse_life_expectancy(life_expectancy_value)
    today = as_of or date.today()
    death_date = estimate_death_date(birthdate, life_expectancy)

    lived_days = max(0, (today - birthdate).days)
    total_days = max(1, (death_date - birthdate).days)
    total_weeks = max(1, ceil(total_days / 7))
    weeks_lived = min(total_weeks, lived_days // 7)
    weeks_remaining = max(0, total_weeks - weeks_lived)
    age_years = lived_days / DAYS_PER_YEAR

    visible_events = []
    for event in sorted(EVENTS, key=lambda item: item["age"]):
        if event["age"] <= life_expectancy:
            visible_events.append(
                {
                    **event,
                    "week_index": min(total_weeks - 1, event["age"] * 52),
                }
            )

    return {
        "birthdate": birthdate.isoformat(),
        "life_expectancy": round(life_expectancy, 2),
        "today": today.isoformat(),
        "death_date": death_date.isoformat(),
        "age_years": round(age_years, 1),
        "total_weeks": total_weeks,
        "weeks_lived": weeks_lived,
        "weeks_remaining": weeks_remaining,
        "percent_used": round((weeks_lived / total_weeks) * 100, 1),
        "events": visible_events,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/calculate", methods=["POST"])
def calculate():
    payload = request.get_json(silent=True) or {}

    try:
        stats = calculate_life_stats(
            payload.get("birthdate", ""),
            payload.get("life_expectancy", ""),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(stats)


@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "service": "weeks-to-live"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

