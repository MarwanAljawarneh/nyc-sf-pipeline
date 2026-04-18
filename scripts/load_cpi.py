import os
import psycopg2
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


def load_cpi(results: list[dict]) -> None:
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
                INSERT INTO raw_cpi (city, date, cpi, period_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (city, date) DO NOTHING
                """,
                (
                    row["city"],
                    row["date"],
                    row["cpi"],
                    row["period_name"],
                ),
            )
            if cursor.rowcount == 1:
                inserted += 1
                logger.success(f"Inserted {row['city'].upper()} {row['date']} — CPI: {row['cpi']}")
            else:
                skipped += 1
                logger.warning(f"Skipped {row['city'].upper()} {row['date']} — already exists")

        except Exception as e:
            logger.error(f"Failed to insert {row['city']} {row['date']}: {e}")
            conn.rollback()

    conn.commit()
    cursor.close()
    conn.close()

    logger.info(f"Done — {inserted} inserted, {skipped} skipped")


if __name__ == "__main__":
    from extract_cpi import extract_cpi
    results = extract_cpi()
    load_cpi(results)