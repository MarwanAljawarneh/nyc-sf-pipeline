import os
from contextlib import closing

import psycopg2
import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def extract_weather():
    cities = {
        "nyc": {"latitude": 40.7128, "longitude": -74.0060},
        "sf": {"latitude": 37.7749, "longitude": -122.4194},
    }

    results = []

    for city, coords in cities.items():
        logger.info(f"Extracting weather for {city.upper()}...")

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "America/New_York" if city == "nyc" else "America/Los_Angeles",
            "forecast_days": 1,
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        temp_max_c = data["daily"]["temperature_2m_max"][0]
        temp_min_c = data["daily"]["temperature_2m_min"][0]

        result = {
            "city": city,
            "date": data["daily"]["time"][0],
            "temp_max_c": temp_max_c,
            "temp_min_c": temp_min_c,
            "temp_max_f": round((temp_max_c * 9 / 5) + 32, 1),
            "temp_min_f": round((temp_min_c * 9 / 5) + 32, 1),
            "precipitation_mm": data["daily"]["precipitation_sum"][0],
        }

        results.append(result)
        logger.success(
            f"Date: {result['date']} {city.upper()}: Temperature Max: {temp_max_c}°C / {result['temp_max_f']}°F, "
            f"Temperature Min: {temp_min_c}°C / {result['temp_min_f']}°F, "
            f"precip: {result['precipitation_mm']}mm"
        )

    return results


def load_weather(results: list[dict]) -> None:
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
                        INSERT INTO raw_weather (city, date, temp_max_c, temp_min_c, temp_max_f, temp_min_f, precipitation_mm)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (city, date) DO NOTHING
                        """,
                        (row["city"], row["date"], row["temp_max_c"], row["temp_min_c"], row["temp_max_f"], row["temp_min_f"], row["precipitation_mm"]),
                    )
                    if cursor.rowcount == 1:
                        inserted += 1
                        logger.success(f"Inserted {row['city'].upper()} for {row['date']}")
                    else:
                        skipped += 1
                        logger.info(f"Skipped existing {row['city'].upper()} for {row['date']}")

    logger.info(f"Done — {inserted} inserted, {skipped} skipped")
