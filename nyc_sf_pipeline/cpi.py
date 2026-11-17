import os
from contextlib import closing
from datetime import datetime

import psycopg2
import requests
from dotenv import load_dotenv
from loguru import logger

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
    response = requests.post(BLS_API_URL, json=payload, timeout=15)
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


def load_cpi(results: list[dict]) -> None:
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        raise ValueError("SUPABASE_DB_URL not found in environment variables")

    inserted = 0
    skipped = 0

    # Commit the entire batch, or roll it all back if any row fails.
    # closing() also releases the connection after commit/rollback.
    with closing(psycopg2.connect(db_url)) as conn:
        with conn:
            with conn.cursor() as cursor:
                for row in results:
                    cursor.execute(
                        """
                        INSERT INTO raw_cpi (city, date, cpi, period_name)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (city, date) DO NOTHING
                        """,
                        (row["city"], row["date"], row["cpi"], row["period_name"]),
                    )
                    if cursor.rowcount == 1:
                        inserted += 1
                        logger.success(f"Inserted {row['city'].upper()} for {row['date']}")
                    else:
                        skipped += 1
                        logger.info(f"Skipped existing {row['city'].upper()} for {row['date']}")

    logger.info(f"Done — {inserted} inserted, {skipped} skipped")
