import os
import psycopg2
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


def load_weather(results: list[dict]) -> None:
    db_url = os.getenv("SUPABASE_DB_URL")
    
    if not db_url:
        raise ValueError("SUPABASE_DB_URL not found in environment variables")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    for row in results:
        try:
            cursor.execute(
                """
                INSERT INTO raw_weather (
                    city, date, temp_max_c, temp_min_c,
                    temp_max_f, temp_min_f, precipitation_mm
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (city, date) DO NOTHING
                """,
                (
                    row["city"],
                    row["date"],
                    row["temp_max_c"],
                    row["temp_min_c"],
                    row["temp_max_f"],
                    row["temp_min_f"],
                    row["precipitation_mm"],
                ),
            )
            if cursor.rowcount == 1:
                inserted += 1
                logger.success(f"Inserted {row['city'].upper()} for {row['date']}")
            else:
                skipped += 1
                logger.warning(f"Skipped {row['city'].upper()} for {row['date']} — already exists")

        except Exception as e:
            logger.error(f"Failed to insert {row['city']} for {row['date']}: {e}")
            conn.rollback()

    conn.commit()
    cursor.close()
    conn.close()

    logger.info(f"Done — {inserted} inserted, {skipped} skipped")


if __name__ == "__main__":
    from extract_weather import extract_weather
    results = extract_weather()
    load_weather(results)