"""Load weather records into Supabase as one atomic transaction."""

import os
from contextlib import closing

import psycopg2
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


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


if __name__ == "__main__":
    from extract_weather import extract_weather

    load_weather(extract_weather())
