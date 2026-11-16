"""Tests for Open-Meteo extraction without live HTTP requests."""

import pytest
import requests

from scripts.extract_weather import extract_weather


class FakeWeatherResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "daily": {
                "time": ["2026-11-15"],
                "temperature_2m_max": [20.0],
                "temperature_2m_min": [10.0],
                "precipitation_sum": [2.5],
            }
        }


def test_weather_extracts_both_cities_with_local_timezones(monkeypatch):
    calls = []

    def fake_get(url, params, timeout):
        calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeWeatherResponse()

    monkeypatch.setattr(requests, "get", fake_get)

    result = extract_weather()

    assert [row["city"] for row in result] == ["nyc", "sf"]
    assert [row["date"] for row in result] == ["2026-11-15", "2026-11-15"]
    assert all(row["temp_max_f"] == 68.0 for row in result)
    assert all(row["temp_min_f"] == 50.0 for row in result)
    assert all(row["precipitation_mm"] == 2.5 for row in result)
    assert [call["params"]["timezone"] for call in calls] == [
        "America/New_York",
        "America/Los_Angeles",
    ]
    assert all(call["timeout"] == 15 for call in calls)


def test_weather_propagates_api_timeout(monkeypatch):
    def fake_get(url, params, timeout):
        raise requests.exceptions.Timeout("Open-Meteo did not respond")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(requests.exceptions.Timeout):
        extract_weather()
