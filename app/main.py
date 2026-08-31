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
    {
        "id": "malala-yousafzai-nobel-peace-prize",
        "name": "Malala Yousafzai Receives Nobel Peace Prize",
        "age": 17.41,
        "color": "#db2777",
        "date": "December 10, 2014",
    },
    {
        "id": "jane-goodall-arrives-at-gombe",
        "name": "Jane Goodall Arrives at Gombe",
        "age": 26.28,
        "color": "#0f766e",
        "date": "July 14, 1960",
    },
    {
        "id": "einstein-special-relativity",
        "name": "Einstein Publishes Special Relativity",
        "age": 26.29,
        "color": "#4f46e5",
        "date": "June 30, 1905",
    },
    {
        "id": "stanton-seneca-falls-convention",
        "name": "Elizabeth Cady Stanton Seneca Falls Convention",
        "age": 32.69,
        "color": "#ea580c",
        "date": "July 19, 1848",
    },
    {
        "id": "rosalind-franklin-dna-paper",
        "name": "Rosalind Franklin DNA Paper Published",
        "age": 32.75,
        "color": "#7c3aed",
        "date": "April 25, 1953",
    },
    {
        "id": "florence-nightingale-scutari",
        "name": "Florence Nightingale Arrives at Scutari",
        "age": 34.48,
        "color": "#be123c",
        "date": "November 4, 1854",
    },
    {
        "id": "marie-curie-nobel-physics",
        "name": "Marie Curie Awarded Nobel Prize in Physics",
        "age": 36.09,
        "color": "#9333ea",
        "date": "December 10, 1903",
    },
    {
        "id": "jonas-salk-polio-vaccine-announced",
        "name": "Jonas Salk Polio Vaccine Announced",
        "age": 40.46,
        "color": "#0284c7",
        "date": "April 12, 1955",
    },
    {
        "id": "grace-hopper-first-computer-bug",
        "name": "Grace Hopper's Team Logs First Computer Bug",
        "age": 40.75,
        "color": "#ca8a04",
        "date": "September 9, 1947",
    },
    {
        "id": "alexander-fleming-discovers-penicillin",
        "name": "Alexander Fleming Discovers Penicillin",
        "age": 47.14,
        "color": "#059669",
        "date": "September 28, 1928",
    },
    {
        "id": "darwin-origin-of-species",
        "name": "Darwin Publishes Origin of Species",
        "age": 50.78,
        "color": "#65a30d",
        "date": "November 24, 1859",
    },
    {
        "id": "susan-b-anthony-votes",
        "name": "Susan B. Anthony Casts Her Vote",
        "age": 52.72,
        "color": "#d946ef",
        "date": "November 5, 1872",
    },
    {
        "id": "desmond-tutu-nobel-peace-prize",
        "name": "Desmond Tutu Receives Nobel Peace Prize",
        "age": 53.18,
        "color": "#1d4ed8",
        "date": "December 10, 1984",
    },
    {
        "id": "rachel-carson-silent-spring",
        "name": "Rachel Carson Publishes Silent Spring",
        "age": 55.34,
        "color": "#15803d",
        "date": "September 27, 1962",
    },
    {
        "id": "clara-barton-american-red-cross",
        "name": "Clara Barton Founds American Red Cross",
        "age": 59.4,
        "color": "#b91c1c",
        "date": "May 21, 1881",
    },
    {
        "id": "louis-pasteur-rabies-vaccination",
        "name": "Pasteur First Human Rabies Vaccination",
        "age": 62.53,
        "color": "#0e7490",
        "date": "July 6, 1885",
    },
    {
        "id": "eleanor-roosevelt-udhr-adoption",
        "name": "Eleanor Roosevelt Leads UDHR Adoption",
        "age": 64.16,
        "color": "#7e22ce",
        "date": "December 10, 1948",
    },
    {
        "id": "wangari-maathai-nobel-peace-prize",
        "name": "Wangari Maathai Receives Nobel Peace Prize",
        "age": 64.69,
        "color": "#047857",
        "date": "December 10, 2004",
    },
    {
        "id": "nelson-mandela-inaugurated-president",
        "name": "Nelson Mandela Inaugurated President",
        "age": 75.81,
        "color": "#f97316",
        "date": "May 10, 1994",
    },
    {
        "id": "barbara-mcclintock-nobel-prize",
        "name": "Barbara McClintock Receives Nobel Prize",
        "age": 81.49,
        "color": "#14b8a6",
        "date": "December 10, 1983",
    },
    {
        "id": "newton-principia-published",
        "name": "Newton Publishes Principia",
        "age": 44.5,
        "color": "#4338ca",
        "date": "July 5, 1687",
    },
    {
        "id": "maxwell-electromagnetic-field-theory",
        "name": "Maxwell Presents Electromagnetic Field Theory",
        "age": 33.49,
        "color": "#0f766e",
        "date": "December 8, 1864",
    },
    {
        "id": "mendel-pea-experiments",
        "name": "Mendel Presents Pea Experiments",
        "age": 42.56,
        "color": "#65a30d",
        "date": "February 8, 1865",
    },
    {
        "id": "mendeleev-periodic-table",
        "name": "Mendeleev Presents the Periodic Table",
        "age": 35.07,
        "color": "#ea580c",
        "date": "March 6, 1869",
    },
    {
        "id": "rontgen-discovers-x-rays",
        "name": "Rontgen Discovers X-Rays",
        "age": 50.62,
        "color": "#0891b2",
        "date": "November 8, 1895",
    },
    {
        "id": "becquerel-discovers-radioactivity",
        "name": "Becquerel Discovers Radioactivity",
        "age": 43.21,
        "color": "#a16207",
        "date": "March 1, 1896",
    },
    {
        "id": "planck-quantum-hypothesis",
        "name": "Planck Presents the Quantum Hypothesis",
        "age": 42.64,
        "color": "#7c3aed",
        "date": "December 14, 1900",
    },
    {
        "id": "ramanujan-letter-to-hardy",
        "name": "Ramanujan Sends His Letter to Hardy",
        "age": 25.07,
        "color": "#be123c",
        "date": "January 16, 1913",
    },
    {
        "id": "noether-theorem-presented",
        "name": "Noether's Theorem Is Presented",
        "age": 36.34,
        "color": "#4f46e5",
        "date": "July 26, 1918",
    },
    {
        "id": "heisenberg-uncertainty-paper",
        "name": "Heisenberg Submits Uncertainty Principle Paper",
        "age": 25.3,
        "color": "#0284c7",
        "date": "March 23, 1927",
    },
    {
        "id": "dirac-equation-paper-received",
        "name": "Dirac Equation Paper Is Received",
        "age": 25.4,
        "color": "#9333ea",
        "date": "January 2, 1928",
    },
    {
        "id": "hubble-expanding-universe-paper",
        "name": "Hubble Publishes Expanding Universe Paper",
        "age": 39.31,
        "color": "#0e7490",
        "date": "March 15, 1929",
    },
    {
        "id": "turing-computable-numbers",
        "name": "Turing's Computable Numbers Paper Is Received",
        "age": 23.93,
        "color": "#2563eb",
        "date": "May 28, 1936",
    },
    {
        "id": "zuse-z3-presented",
        "name": "Zuse Presents the Z3 Computer",
        "age": 30.89,
        "color": "#b45309",
        "date": "May 12, 1941",
    },
    {
        "id": "eniac-unveiled",
        "name": "Eckert and Mauchly Unveil ENIAC",
        "age": 26.85,
        "color": "#1d4ed8",
        "date": "February 14, 1946",
    },
    {
        "id": "transistor-first-tested",
        "name": "Bardeen and Brattain Test the First Transistor",
        "age": 39.57,
        "color": "#059669",
        "date": "December 16, 1947",
    },
    {
        "id": "manchester-baby-first-program",
        "name": "Manchester Baby Runs the First Stored Program",
        "age": 36.99,
        "color": "#7e22ce",
        "date": "June 21, 1948",
    },
    {
        "id": "wu-parity-violation-paper",
        "name": "Wu Publishes Parity Violation Experiment",
        "age": 44.71,
        "color": "#db2777",
        "date": "February 15, 1957",
    },
    {
        "id": "kilby-integrated-circuit",
        "name": "Kilby Demonstrates the Integrated Circuit",
        "age": 34.85,
        "color": "#ca8a04",
        "date": "September 12, 1958",
    },
    {
        "id": "higgs-boson-paper-received",
        "name": "Higgs Boson Paper Is Received",
        "age": 35.26,
        "color": "#c026d3",
        "date": "August 31, 1964",
    },
    {
        "id": "arpanet-first-message",
        "name": "Kleinrock's Lab Sends First ARPANET Message",
        "age": 35.38,
        "color": "#0369a1",
        "date": "October 29, 1969",
    },
    {
        "id": "intel-4004-debut",
        "name": "Faggin's Intel 4004 Microprocessor Debuts",
        "age": 29.96,
        "color": "#c2410c",
        "date": "November 15, 1971",
    },
    {
        "id": "tcp-ip-three-network-test",
        "name": "Cerf and Kahn's TCP/IP Passes Three-Network Test",
        "age": 34.42,
        "color": "#047857",
        "date": "November 22, 1977",
    },
    {
        "id": "berners-lee-www-proposal",
        "name": "Berners-Lee Writes the World Wide Web Proposal",
        "age": 33.76,
        "color": "#7c2d12",
        "date": "March 12, 1989",
    },
    {
        "id": "torvalds-linux-announcement",
        "name": "Torvalds Announces Linux",
        "age": 21.66,
        "color": "#111827",
        "date": "August 25, 1991",
    },
    {
        "id": "wiles-fermat-proof-announcement",
        "name": "Wiles Announces Fermat's Last Theorem Proof",
        "age": 40.2,
        "color": "#15803d",
        "date": "June 23, 1993",
    },
    {
        "id": "perelman-ricci-flow-preprint",
        "name": "Perelman Posts Ricci Flow Preprint",
        "age": 36.41,
        "color": "#b91c1c",
        "date": "November 11, 2002",
    },
    {
        "id": "doudna-charpentier-crispr-cas9",
        "name": "Doudna and Charpentier Publish CRISPR-Cas9 Paper",
        "age": 48.36,
        "color": "#14b8a6",
        "date": "June 28, 2012",
    },
    {
        "id": "alphago-defeats-lee-sedol",
        "name": "Hassabis's AlphaGo Defeats Lee Sedol",
        "age": 39.63,
        "color": "#6d28d9",
        "date": "March 15, 2016",
    },
    {
        "id": "alphafold2-casp14-breakthrough",
        "name": "Hassabis's AlphaFold2 Solves CASP14 Protein Challenge",
        "age": 44.35,
        "color": "#0d9488",
        "date": "November 30, 2020",
    },
]

DAYS_PER_YEAR = 365.2425
MAX_LIFE_EXPECTANCY = 130
MAX_EVENT_NAME_LENGTH = 140
MAX_EVENT_DATE_LABEL_LENGTH = 80
MAX_PERSONAL_EVENT_NAME_LENGTH = 200
MAX_PERSONAL_EVENT_DETAILS_LENGTH = 4000
MAX_PERSONAL_EVENT_TIMELINES_LENGTH = 400
DEFAULT_PERSONAL_EVENT_COLOR = "#f97316"
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
COLOR_KEYS = ("lived", "remaining", "personal", "historical")
DEFAULT_COLORS = {
    "lived": "#334155",       # Lived weeks (--spent)
    "remaining": "#f6d365",   # Remaining weeks (--future)
    "personal": "#f97316",    # Personal Event dots (--personal) — orange by default
    "historical": "#ef4444",  # Historical Figure Milestone dots (--event)
}
DEFAULT_SETTINGS = {
    "birthdate": "1980-09-08",
    "life_expectancy": 78.6,
    "colors": dict(DEFAULT_COLORS),
}
DEFAULT_EVENT_MIGRATIONS = {
    "2026-07-historical-events": [
        "malala-yousafzai-nobel-peace-prize",
        "jane-goodall-arrives-at-gombe",
        "einstein-special-relativity",
        "stanton-seneca-falls-convention",
        "rosalind-franklin-dna-paper",
        "florence-nightingale-scutari",
        "marie-curie-nobel-physics",
        "jonas-salk-polio-vaccine-announced",
        "grace-hopper-first-computer-bug",
        "alexander-fleming-discovers-penicillin",
        "darwin-origin-of-species",
        "susan-b-anthony-votes",
        "desmond-tutu-nobel-peace-prize",
        "rachel-carson-silent-spring",
        "clara-barton-american-red-cross",
        "louis-pasteur-rabies-vaccination",
        "eleanor-roosevelt-udhr-adoption",
        "wangari-maathai-nobel-peace-prize",
        "nelson-mandela-inaugurated-president",
        "barbara-mcclintock-nobel-prize",
    ],
    "2026-07-science-math-computing-events": [
        "newton-principia-published",
        "maxwell-electromagnetic-field-theory",
        "mendel-pea-experiments",
        "mendeleev-periodic-table",
        "rontgen-discovers-x-rays",
        "becquerel-discovers-radioactivity",
        "planck-quantum-hypothesis",
        "ramanujan-letter-to-hardy",
        "noether-theorem-presented",
        "heisenberg-uncertainty-paper",
        "dirac-equation-paper-received",
        "hubble-expanding-universe-paper",
        "turing-computable-numbers",
        "zuse-z3-presented",
        "eniac-unveiled",
        "transistor-first-tested",
        "manchester-baby-first-program",
        "wu-parity-violation-paper",
        "kilby-integrated-circuit",
        "higgs-boson-paper-received",
        "arpanet-first-message",
        "intel-4004-debut",
        "tcp-ip-three-network-test",
        "berners-lee-www-proposal",
        "torvalds-linux-announcement",
        "wiles-fermat-proof-announcement",
        "perelman-ricci-flow-preprint",
        "doudna-charpentier-crispr-cas9",
        "alphago-defeats-lee-sedol",
        "alphafold2-casp14-breakthrough",
    ],
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


def event_migrations_path() -> Path:
    return data_dir() / "event_migrations.json"


def normalize_event_id(value: str | None = None) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", (value or "").lower()).strip("-")
    return cleaned or uuid4().hex


def sorted_events(events: list[dict]) -> list[dict]:
    return sorted(events, key=lambda item: (float(item["age"]), item["name"].lower()))


def seed_events() -> list[dict]:
    return sorted_events([dict(event) for event in DEFAULT_EVENTS])


def load_event_migrations() -> set[str]:
    path = event_migrations_path()
    if not path.exists():
        return set()

    with path.open("r", encoding="utf-8") as handle:
        raw_migrations = json.load(handle)

    if not isinstance(raw_migrations, list):
        return set()

    return {str(migration_id) for migration_id in raw_migrations}


def write_event_migrations(migration_ids: set[str]) -> None:
    path = event_migrations_path()
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(sorted(migration_ids), handle, indent=2)
        handle.write("\n")
    tmp_path.replace(path)


def mark_default_event_migrations_applied() -> None:
    applied = load_event_migrations()
    updated = applied | set(DEFAULT_EVENT_MIGRATIONS)
    if updated != applied:
        write_event_migrations(updated)


def apply_default_event_migrations(events: list[dict]) -> list[dict]:
    default_events_by_id = {event["id"]: event for event in DEFAULT_EVENTS}
    applied = load_event_migrations()
    seen_ids = {event["id"] for event in events}
    migrated_events = False
    migrated_ids = False

    for migration_id, event_ids in DEFAULT_EVENT_MIGRATIONS.items():
        if migration_id in applied:
            continue

        for event_id in event_ids:
            if event_id in seen_ids:
                continue
            event = default_events_by_id.get(event_id)
            if event is None:
                continue
            events.append(dict(event))
            seen_ids.add(event_id)
            migrated_events = True

        applied.add(migration_id)
        migrated_ids = True

    if migrated_events:
        write_events(events)
    if migrated_ids:
        write_event_migrations(applied)

    return sorted_events(events)


def load_events() -> list[dict]:
    path = events_path()
    if not path.exists():
        events = seed_events()
        write_events(events)
        mark_default_event_migrations_applied()
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
    return apply_default_event_migrations(events)


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


def personal_events_path() -> Path:
    return data_dir() / "personal_events.json"


def clean_optional_text(value: str | None, field_name: str, max_length: int) -> str:
    text = (value or "").strip()
    if len(text) > max_length:
        raise ValueError(f"{field_name} cannot exceed {max_length} characters.")
    return text


def parse_iso_date(value: str | None, field_name: str) -> date:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD.") from exc


def parse_bool(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() not in {"", "0", "false", "no", "off"}


def validate_personal_event(payload: dict, event_id: str | None = None) -> dict:
    name = clean_text(payload.get("name"), "Event name", MAX_PERSONAL_EVENT_NAME_LENGTH)
    start = parse_iso_date(payload.get("date"), "Start date")

    end_raw = (payload.get("end_date") or "").strip()
    end = parse_iso_date(end_raw, "End date") if end_raw else start
    if end < start:
        raise ValueError("End date cannot be before the start date.")

    details = clean_optional_text(payload.get("details"), "Details", MAX_PERSONAL_EVENT_DETAILS_LENGTH)
    timelines = clean_optional_text(payload.get("timelines"), "Timelines", MAX_PERSONAL_EVENT_TIMELINES_LENGTH)

    color = (payload.get("color") or DEFAULT_PERSONAL_EVENT_COLOR).strip() or DEFAULT_PERSONAL_EVENT_COLOR
    if not HEX_COLOR_RE.fullmatch(color):
        raise ValueError("Event color must be a 6-digit hex color.")

    return {
        "id": normalize_event_id(event_id or payload.get("id") or name),
        "name": name,
        "date": start.isoformat(),
        "end_date": end.isoformat(),
        "details": details,
        "timelines": timelines,
        "color": color.lower(),
        "enabled": parse_bool(payload.get("enabled"), default=True),
    }


def sorted_personal_events(events: list[dict]) -> list[dict]:
    return sorted(events, key=lambda item: (item["date"], item["end_date"], item["name"].lower()))


def load_personal_events() -> list[dict]:
    path = personal_events_path()
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as handle:
        raw_events = json.load(handle)

    if not isinstance(raw_events, list):
        return []

    events = []
    seen_ids = set()
    for event in raw_events:
        if not isinstance(event, dict):
            continue
        try:
            normalized = validate_personal_event(event, event_id=event.get("id"))
        except ValueError:
            continue
        while normalized["id"] in seen_ids:
            normalized["id"] = uuid4().hex
        seen_ids.add(normalized["id"])
        events.append(normalized)
    return sorted_personal_events(events)


def write_personal_events(events: list[dict]) -> None:
    path = personal_events_path()
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(sorted_personal_events(events), handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp_path.replace(path)


def personal_event_week_span(
    birthdate: date, total_weeks: int, start_iso: str, end_iso: str
) -> tuple[int, int] | None:
    start = datetime.strptime(start_iso, "%Y-%m-%d").date()
    end = datetime.strptime(end_iso, "%Y-%m-%d").date()

    start_days = (start - birthdate).days
    end_days = (end - birthdate).days

    # Entirely before birth: no dot on this life's timeline.
    if end_days < 0:
        return None

    start_week = max(0, start_days // 7)
    end_week = end_days // 7

    # Entirely after the projected death date: no dot.
    if start_week > total_weeks - 1:
        return None

    end_week = min(total_weeks - 1, end_week)
    if end_week < start_week:
        return None
    return start_week, end_week


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


def validate_colors(payload) -> dict:
    colors = dict(DEFAULT_COLORS)
    if isinstance(payload, dict):
        for key in COLOR_KEYS:
            value = payload.get(key)
            if value is None:
                continue
            value = str(value).strip()
            if not HEX_COLOR_RE.fullmatch(value):
                raise ValueError(f"{key.capitalize()} color must be a 6-digit hex color.")
            colors[key] = value.lower()
    return colors


def validate_settings(payload: dict) -> dict:
    birthdate = parse_birthdate(payload.get("birthdate", DEFAULT_SETTINGS["birthdate"])).isoformat()
    life_expectancy = parse_life_expectancy(payload.get("life_expectancy", DEFAULT_SETTINGS["life_expectancy"]))
    return {
        "birthdate": birthdate,
        "life_expectancy": round(life_expectancy, 2),
        "colors": validate_colors(payload.get("colors")),
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
    personal_events: list[dict] | None = None,
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

    visible_personal_events = []
    source_personal = personal_events if personal_events is not None else []
    for event in sorted_personal_events(source_personal):
        if not event.get("enabled", True):
            continue
        span = personal_event_week_span(
            birthdate, total_weeks, event["date"], event["end_date"]
        )
        if span is None:
            continue
        start_week, end_week = span
        start_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
        visible_personal_events.append(
            {
                **event,
                "week_start": start_week,
                "week_end": end_week,
                "age_at_start": round(max(0.0, (start_date - birthdate).days / DAYS_PER_YEAR), 1),
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
        "personal_events": visible_personal_events,
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
    # The calculate form only submits birthdate + life_expectancy; keep any saved
    # dot colors so recalculating never resets Settings.
    payload.setdefault("colors", load_settings().get("colors"))

    try:
        settings = validate_settings(payload)
        stats = calculate_life_stats(
            settings["birthdate"],
            settings["life_expectancy"],
            events=load_events(),
            personal_events=load_personal_events(),
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


@app.route("/api/settings", methods=["POST"])
def update_settings():
    incoming = request.get_json(silent=True) or {}
    current = load_settings()
    merged = dict(current)

    for key in ("birthdate", "life_expectancy"):
        if incoming.get(key) is not None:
            merged[key] = incoming[key]

    if isinstance(incoming.get("colors"), dict):
        merged_colors = dict(current.get("colors", DEFAULT_COLORS))
        merged_colors.update({k: v for k, v in incoming["colors"].items() if k in COLOR_KEYS})
        merged["colors"] = merged_colors

    try:
        settings = validate_settings(merged)
        write_settings(settings)
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


@app.route("/api/events/import", methods=["POST"])
def import_events():
    payload = request.get_json(silent=True) or {}
    raw_events = payload.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        return jsonify({"error": "Import requires at least one event row."}), 400

    imported_events = []
    for index, raw_event in enumerate(raw_events, start=2):
        if not isinstance(raw_event, dict):
            return jsonify({"error": f"Row {index}: event row is invalid."}), 400
        row_number = raw_event.get("_row", index)
        try:
            imported_events.append(validate_event(raw_event, event_id=uuid4().hex))
        except ValueError as exc:
            return jsonify({"error": f"Row {row_number}: {exc}"}), 400

    events = load_events()
    events.extend(imported_events)
    write_events(events)
    return jsonify({"imported": len(imported_events), "events": load_events()}), 201


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


@app.route("/api/personal-events", methods=["GET"])
def list_personal_events():
    return jsonify({"personal_events": load_personal_events()})


@app.route("/api/personal-events", methods=["POST"])
def create_personal_event():
    payload = request.get_json(silent=True) or {}
    try:
        event = validate_personal_event(payload, event_id=uuid4().hex)
        events = load_personal_events()
        events.append(event)
        write_personal_events(events)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(event), 201


@app.route("/api/personal-events/import", methods=["POST"])
def import_personal_events():
    payload = request.get_json(silent=True) or {}
    raw_events = payload.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        return jsonify({"error": "Import requires at least one event row."}), 400

    imported_events = []
    for index, raw_event in enumerate(raw_events, start=2):
        if not isinstance(raw_event, dict):
            return jsonify({"error": f"Row {index}: event row is invalid."}), 400
        row_number = raw_event.get("_row", index)
        try:
            imported_events.append(validate_personal_event(raw_event, event_id=uuid4().hex))
        except ValueError as exc:
            return jsonify({"error": f"Row {row_number}: {exc}"}), 400

    events = load_personal_events()
    events.extend(imported_events)
    write_personal_events(events)
    return jsonify({"imported": len(imported_events), "personal_events": load_personal_events()}), 201


@app.route("/api/personal-events/<event_id>", methods=["PUT"])
def update_personal_event(event_id: str):
    events = load_personal_events()
    event_index = next((index for index, event in enumerate(events) if event["id"] == event_id), None)
    if event_index is None:
        return jsonify({"error": "Personal event not found."}), 404

    payload = request.get_json(silent=True) or {}
    try:
        events[event_index] = validate_personal_event(payload, event_id=event_id)
        write_personal_events(events)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(events[event_index])


@app.route("/api/personal-events/<event_id>/toggle", methods=["POST"])
def toggle_personal_event(event_id: str):
    events = load_personal_events()
    event_index = next((index for index, event in enumerate(events) if event["id"] == event_id), None)
    if event_index is None:
        return jsonify({"error": "Personal event not found."}), 404

    payload = request.get_json(silent=True) or {}
    if "enabled" in payload:
        events[event_index]["enabled"] = parse_bool(payload.get("enabled"), default=True)
    else:
        events[event_index]["enabled"] = not events[event_index].get("enabled", True)
    write_personal_events(events)
    return jsonify(events[event_index])


@app.route("/api/personal-events/<event_id>", methods=["DELETE"])
def delete_personal_event(event_id: str):
    events = load_personal_events()
    remaining = [event for event in events if event["id"] != event_id]
    if len(remaining) == len(events):
        return jsonify({"error": "Personal event not found."}), 404
    write_personal_events(remaining)
    return jsonify({"deleted": event_id})


@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "service": "weeks-to-live"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
