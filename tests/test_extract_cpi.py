"""Tests for BLS CPI extraction without a real API key or network calls."""

import pytest
import requests

from scripts.extract_cpi import extract_cpi


class FakeCpiResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "Results": {
                "series": [
                    {
                        "seriesID": "CUURS12ASA0",
                        "data": [
                            {"year": "2026", "period": "M09", "periodName": "September", "value": "325.1"},
                            {"year": "2026", "period": "M10", "periodName": "October", "value": "-"},
                        ],
                    },
                    {
                        "seriesID": "CUURS49BSA0",
                        "data": [
                            {"year": "2026", "period": "M09", "periodName": "September", "value": "345.2"}
                        ],
                    },
                ]
            }
        }


def test_cpi_extracts_rows_and_skips_unavailable_values(monkeypatch):
    request_details = {}

    def fake_post(url, json, timeout):
        request_details.update(url=url, payload=json, timeout=timeout)
        return FakeCpiResponse()

    monkeypatch.setenv("BLS_API_KEY", "test-key")
    monkeypatch.setattr(requests, "post", fake_post)

    result = extract_cpi()

    assert result == [
        {"city": "nyc", "date": "2026-09-01", "cpi": 325.1, "period_name": "September"},
        {"city": "sf", "date": "2026-09-01", "cpi": 345.2, "period_name": "September"},
    ]
    assert request_details["url"].startswith("https://api.bls.gov/")
    assert request_details["payload"]["registrationkey"] == "test-key"
    assert request_details["timeout"] == 15


def test_cpi_requires_api_key(monkeypatch):
    monkeypatch.delenv("BLS_API_KEY", raising=False)

    with pytest.raises(ValueError, match="BLS_API_KEY"):
        extract_cpi()


def test_cpi_propagates_api_timeout(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.exceptions.Timeout("BLS did not respond")

    monkeypatch.setenv("BLS_API_KEY", "test-key")
    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(requests.exceptions.Timeout):
        extract_cpi()
