import os
from contextlib import closing
from io import StringIO

import polars as pl
import psycopg2
import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

ZORI_URL = "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv"

cities = {
    "nyc": "New York, NY",
    "sf": "San Francisco, CA",
}

def extract_housing():
    logger.info("Downloading Zillow ZORI CSV...")

    response = requests.get(ZORI_URL, timeout=30)
    response.raise_for_status()

    df = pl.read_csv(StringIO(response.text))
    logger.info(f"Downloaded {len(df)} metro rows")

    results = []

    for city_key, city_name in cities.items():
        row = df.filter(pl.col("RegionName").str.contains(city_name))

        if row.is_empty():
            logger.warning(f"No data found for {city_name}")
            continue
        
        date_columns = [col for col in df.columns if col.startswith("20")]
        latest_date = date_columns[-1]
        latest_rent = row[latest_date][0]

        result = {
            "city": city_key,
            "date": latest_date,
            "median_rent": round(float(latest_rent), 2),
        }

        results.append(result)
        logger.success(
            f"[{latest_date}] {city_key.upper()}: Median rent ${latest_rent:,.0f}/month"
        )

    return results


def load_housing(results: list[dict]) -> None:
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
                        INSERT INTO raw_housing (city, date, median_rent)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (city, date) DO NOTHING
                        """,
                        (row["city"], row["date"], row["median_rent"]),
                    )
                    if cursor.rowcount == 1:
                        inserted += 1
                        logger.success(f"Inserted {row['city'].upper()} for {row['date']}")
                    else:
                        skipped += 1
                        logger.info(f"Skipped existing {row['city'].upper()} for {row['date']}")

    logger.info(f"Done — {inserted} inserted, {skipped} skipped")
