import requests
import polars as pl
from io import StringIO
from loguru import logger

ZORI_URL = "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv"

cities = {
    "nyc": "New York, NY",
    "sf": "San Francisco, CA",
}


def extract_housing():
    logger.info("Downloading Zillow ZORI CSV...")

    response = requests.get(ZORI_URL)
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


if __name__ == "__main__":
    extract_housing()