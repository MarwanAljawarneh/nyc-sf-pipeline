import os
import requests
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SERIES = {
    "nyc": "CUURS12ASA0",
    "sf": "CUURS49BSA0",
}

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

def extract_cpi():
    end_year = str(datetime.now().year)
    start_year = str(datetime.now().year - 2)

    api_key = os.getenv("BLS_API_KEY")

    if not api_key:
        raise ValueError("BLS_API_KEY not found in environment variables")

    payload = {
        "seriesid": list(SERIES.values()),
        "startyear": start_year,
        "endyear": end_year,
        "registrationkey": api_key,
    }

    logger.info("Fetching CPI data from BLS API...")
    response = requests.post(BLS_API_URL, json=payload)
    response.raise_for_status()
    data = response.json()

    results = []

    for series in data["Results"]["series"]:
        city = next(k for k, v in SERIES.items() if v == series["seriesID"])

        for entry in series["data"]:
            if entry["value"] == "-":
                logger.warning(f"Skipping {city.upper()} {entry['periodName']} {entry['year']} — data unavailable")
                continue

            period = entry["period"].replace("M", "")
            date = f"{entry['year']}-{period.zfill(2)}-01"

            result = {
                "city": city,
                "date": date,
                "cpi": float(entry["value"]),
                "period_name": entry["periodName"],
            }

            results.append(result)
            logger.success(f"[{date}] {city.upper()} CPI: {entry['value']}")

    return results


if __name__ == "__main__":
    extract_cpi()