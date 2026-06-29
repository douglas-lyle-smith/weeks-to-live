from datetime import date

from app.main import app, calculate_life_stats, estimate_death_date


def test_estimate_death_date_for_whole_years():
    assert estimate_death_date(date(1980, 9, 8), 70).isoformat() == "2050-09-08"


def test_calculate_life_stats_returns_expected_counts():
    stats = calculate_life_stats("1980-09-08", "70", as_of=date(2026, 6, 29))

    assert stats["death_date"] == "2050-09-08"
    assert stats["weeks_lived"] == 2390
    assert stats["weeks_remaining"] > 0
    assert stats["total_weeks"] >= stats["weeks_lived"]


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

