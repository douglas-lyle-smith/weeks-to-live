import json
from datetime import date

from app.main import DEFAULT_EVENTS, DEFAULT_EVENT_MIGRATIONS, app, calculate_life_stats, estimate_death_date


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
