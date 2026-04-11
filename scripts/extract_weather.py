import requests
from loguru import logger


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
            "timezone": "America/New_York",
            "forecast_days": 1,
        }

        response = requests.get(url, params=params)
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


if __name__ == "__main__":
    extract_weather()