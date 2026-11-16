"""Tests for Zillow housing extraction with a small in-memory CSV."""

import pytest
import requests

from scripts.extract_housing import extract_housing


SAMPLE_ZORI_CSV = (
    "RegionName,2026-09-30,2026-10-31\n"
    "New York, NY,3000,3100\n"
    "San Francisco, CA,3500,3650\n"
)


class FakeHousingResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def test_housing_extracts_latest_monthly_rent(monkeypatch):
    # Quoted city names contain commas and must remain single CSV fields.
    csv_text = (
        'RegionName,2026-09-30,2026-10-31\n'
        '"New York, NY",3000,3100\n'
        '"San Francisco, CA",3500,3650\n'
    )
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeHousingResponse(csv_text)

    monkeypatch.setattr(requests, "get", fake_get)

    result = extract_housing()

    assert result == [
        {"city": "nyc", "date": "2026-10-31", "median_rent": 3100.0},
        {"city": "sf", "date": "2026-10-31", "median_rent": 3650.0},
    ]
    assert len(calls) == 1
    assert calls[0][1] == 30


def test_housing_propagates_download_timeout(monkeypatch):
    def fake_get(url, timeout):
        raise requests.exceptions.Timeout("Zillow download timed out")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(requests.exceptions.Timeout):
        extract_housing()
