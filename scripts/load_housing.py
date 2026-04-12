import os
import psycopg2
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


def load_housing(results: list[dict]) -> None:
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
                INSERT INTO raw_housing (city, date, median_rent)
                VALUES (%s, %s, %s)
                ON CONFLICT (city, date) DO NOTHING
                """,
                (
                    row["city"],
                    row["date"],
                    row["median_rent"],
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
    from extract_housing import extract_housing
    results = extract_housing()
    load_housing(results)