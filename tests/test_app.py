import json
from datetime import date

from app.main import (
    DEFAULT_EVENTS,
    DEFAULT_EVENT_MIGRATIONS,
    app,
    calculate_life_stats,
    estimate_death_date,
    personal_event_week_span,
)


def test_estimate_death_date_for_whole_years():
    assert estimate_death_date(date(1980, 9, 8), 70).isoformat() == "2050-09-08"


def test_calculate_life_stats_returns_expected_counts():
    stats = calculate_life_stats("1980-09-08", "70", as_of=date(2026, 6, 29))

    assert stats["death_date"] == "2050-09-08"
    assert stats["age_columns"] == (stats["total_weeks"] + 51) // 52
    assert stats["weeks_lived"] == 2390
    assert stats["weeks_remaining"] > 0
    assert stats["total_weeks"] >= stats["weeks_lived"]


def test_calculate_api_persists_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    client = app.test_client()

    response = client.post(
        "/api/calculate",
        json={"birthdate": "1990-01-02", "life_expectancy": 81.5},
    )
    settings_response = client.get("/api/settings")

    assert response.status_code == 200
    assert settings_response.status_code == 200
    assert settings_response.get_json() == {
        "birthdate": "1990-01-02",
        "life_expectancy": 81.5,
    }


def test_event_crud_persists_to_json(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    client = app.test_client()

    create_response = client.post(
        "/api/events",
        json={
            "name": "Test Milestone",
            "age": 12.5,
            "date": "Test Date",
            "color": "#123abc",
        },
    )
    assert create_response.status_code == 201
    event = create_response.get_json()

    update_response = client.put(
        f"/api/events/{event['id']}",
        json={
            "name": "Updated Milestone",
            "age": 13,
            "date": "Updated Date",
            "color": "#abcdef",
        },
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["id"] == event["id"]

    list_response = client.get("/api/events")
    updated = [item for item in list_response.get_json()["events"] if item["id"] == event["id"]][0]
    assert updated["name"] == "Updated Milestone"
    assert updated["age"] == 13

    delete_response = client.delete(f"/api/events/{event['id']}")
    assert delete_response.status_code == 200
    assert event["id"] not in {item["id"] for item in client.get("/api/events").get_json()["events"]}


def test_event_import_appends_valid_rows(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    client = app.test_client()

    response = client.post(
        "/api/events/import",
        json={
            "events": [
                {"name": "CSV Milestone", "age": 10, "date": "First import", "color": "#112233"},
                {"name": "CSV Decimal", "age": 12.5, "date": "Second import", "color": "#445566"},
            ]
        },
    )
    events = client.get("/api/events").get_json()["events"]

    assert response.status_code == 201
    assert response.get_json()["imported"] == 2
    assert {"CSV Milestone", "CSV Decimal"}.issubset({event["name"] for event in events})


def test_event_import_rejects_bad_row_without_partial_write(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    client = app.test_client()
    before_events = client.get("/api/events").get_json()["events"]

    response = client.post(
        "/api/events/import",
        json={
            "events": [
                {"name": "Good CSV Row", "age": 11, "date": "Good", "color": "#123abc"},
                {"name": "Bad CSV Row", "age": "not-a-number", "date": "Bad", "color": "#abcdef"},
            ]
        },
    )
    after_events = client.get("/api/events").get_json()["events"]

    assert response.status_code == 400
    assert "Row 3" in response.get_json()["error"]
    assert after_events == before_events


def test_existing_event_file_gets_default_event_migration_once(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    migrated_event_ids = DEFAULT_EVENT_MIGRATIONS["2026-07-historical-events"]
    legacy_event = {
        "id": "legacy-custom-event",
        "name": "Legacy Custom Event",
        "age": 10,
        "date": "Already persisted",
        "color": "#123abc",
    }
    (tmp_path / "events.json").write_text(json.dumps([legacy_event]), encoding="utf-8")
    client = app.test_client()

    migrated_ids = {event["id"] for event in client.get("/api/events").get_json()["events"]}
    assert "legacy-custom-event" in migrated_ids
    assert set(migrated_event_ids).issubset(migrated_ids)
    assert "jesus-crucified" not in migrated_ids

    delete_response = client.delete(f"/api/events/{migrated_event_ids[0]}")
    reloaded_ids = {event["id"] for event in client.get("/api/events").get_json()["events"]}
    assert delete_response.status_code == 200
    assert migrated_event_ids[0] not in reloaded_ids


def test_default_event_migrations_reference_default_events():
    default_ids = {event["id"] for event in DEFAULT_EVENTS}
    migrated_ids = {
        event_id
        for event_ids in DEFAULT_EVENT_MIGRATIONS.values()
        for event_id in event_ids
    }

    assert migrated_ids.issubset(default_ids)


def test_fresh_seed_marks_default_event_migrations_applied(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    migrated_event_id = DEFAULT_EVENT_MIGRATIONS["2026-07-historical-events"][0]
    client = app.test_client()

    assert migrated_event_id in {event["id"] for event in client.get("/api/events").get_json()["events"]}
    delete_response = client.delete(f"/api/events/{migrated_event_id}")
    reloaded_ids = {event["id"] for event in client.get("/api/events").get_json()["events"]}

    assert delete_response.status_code == 200
    assert migrated_event_id not in reloaded_ids


def test_personal_event_week_span_single_and_range():
    birthdate = date(1980, 9, 8)
    total_weeks = 5000

    # Same-day event lands on one week.
    single = personal_event_week_span(birthdate, total_weeks, "2015-12-02", "2015-12-02")
    assert single is not None
    assert single[0] == single[1]

    # A multi-week span covers more than one week-dot.
    span = personal_event_week_span(birthdate, total_weeks, "2024-06-22", "2024-07-20")
    assert span is not None
    assert span[1] > span[0]

    # Entirely before birth has no dot on this timeline.
    assert personal_event_week_span(birthdate, total_weeks, "1977-08-26", "1977-08-26") is None


def test_personal_event_before_birth_clamps_start():
    birthdate = date(1980, 9, 8)
    span = personal_event_week_span(birthdate, 5000, "1980-09-01", "1980-09-20")
    assert span is not None
    assert span[0] == 0


def test_personal_event_crud_and_toggle(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    client = app.test_client()

    assert client.get("/api/personal-events").get_json()["personal_events"] == []

    create = client.post(
        "/api/personal-events",
        json={
            "name": "Smith Family OBX Vacation",
            "date": "2024-06-22",
            "end_date": "2024-06-29",
            "details": "Le Taha - #1186",
            "color": "#2563eb",
        },
    )
    assert create.status_code == 201
    event = create.get_json()
    assert event["enabled"] is True
    assert event["end_date"] == "2024-06-29"

    toggle = client.post(f"/api/personal-events/{event['id']}/toggle", json={"enabled": False})
    assert toggle.status_code == 200
    assert toggle.get_json()["enabled"] is False

    update = client.put(
        f"/api/personal-events/{event['id']}",
        json={"name": "OBX 2024", "date": "2024-06-22", "end_date": "2024-06-30", "color": "#16a34a"},
    )
    assert update.status_code == 200
    assert update.get_json()["end_date"] == "2024-06-30"

    delete = client.delete(f"/api/personal-events/{event['id']}")
    assert delete.status_code == 200
    assert client.get("/api/personal-events").get_json()["personal_events"] == []


def test_personal_event_rejects_end_before_start(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    client = app.test_client()
    response = client.post(
        "/api/personal-events",
        json={"name": "Bad range", "date": "2020-05-10", "end_date": "2020-05-01"},
    )
    assert response.status_code == 400
    assert "End date" in response.get_json()["error"]


def test_personal_event_import_and_calculate_span(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    client = app.test_client()

    imported = client.post(
        "/api/personal-events/import",
        json={
            "events": [
                {"date": "1980-09-08", "end_date": "", "name": "Doug Smith - Born", "details": "Little Rock, AR"},
                {"date": "2024-06-22", "end_date": "2024-06-29", "name": "OBX Vacation", "timelines": "Doug Smith", "details": "Le Taha"},
            ]
        },
    )
    assert imported.status_code == 201
    assert imported.get_json()["imported"] == 2

    stats = calculate_life_stats(
        "1980-09-08",
        "78.6",
        personal_events=client.get("/api/personal-events").get_json()["personal_events"],
        as_of=date(2026, 8, 31),
    )
    by_name = {event["name"]: event for event in stats["personal_events"]}
    assert by_name["Doug Smith - Born"]["week_start"] == 0
    assert by_name["OBX Vacation"]["week_end"] > by_name["OBX Vacation"]["week_start"]


def test_disabled_personal_event_excluded_from_chart(tmp_path, monkeypatch):
    monkeypatch.setenv("WEEKS_TO_LIVE_DATA_DIR", str(tmp_path))
    client = app.test_client()
    created = client.post(
        "/api/personal-events",
        json={"name": "Hidden", "date": "2015-01-01", "enabled": False},
    ).get_json()

    stats = calculate_life_stats(
        "1980-09-08",
        "78.6",
        personal_events=client.get("/api/personal-events").get_json()["personal_events"],
        as_of=date(2026, 8, 31),
    )
    assert created["id"] not in {event["id"] for event in stats["personal_events"]}


def test_index_includes_personal_events_ui():
    client = app.test_client()
    html = client.get("/").get_data(as_text=True)
    assert 'id="show-personal-events-toggle"' in html
    assert "Historical Figure Milestones" in html
    assert 'data-tab="personal"' in html


def test_calculate_api_rejects_future_birthdate():
    client = app.test_client()
    response = client.post(
        "/api/calculate",
        json={"birthdate": "2999-01-01", "life_expectancy": 80},
    )

    assert response.status_code == 400
    assert "future" in response.get_json()["error"]


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_index_uses_versioned_static_assets():
    client = app.test_client()
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "/static/css/style.css?v=" in html
    assert "/static/js/main.js?v=" in html


def test_index_includes_events_visibility_toggle():
    client = app.test_client()
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="show-events-toggle"' in html
    assert 'role="switch"' in html
