import os
from typing import Optional
from datetime import datetime, timedelta

from dotenv import load_dotenv
import requests
from models import HistoricalWeatherApiResponse

load_dotenv()

WEATHERAPI_KEY = os.getenv("API_KEY")  # WeatherAPI.com API key
DATE = datetime.now().strftime("%Y-%m-%d")  # Today's date

def fetch_weather_data(city: str, date: str) -> Optional[HistoricalWeatherApiResponse]:
    """
    Fetches historical weather data from the WeatherAPI for a given city and date.
    """
    api_url = f"http://api.weatherapi.com/v1/history.json?key={WEATHERAPI_KEY}&q={city}&dt={date}&aqi=no&alerts=no"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        # Validate and parse with Pydantic
        weather_data = HistoricalWeatherApiResponse.model_validate(data)
        return weather_data
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed for {city} on {date}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching data for {city} on {date}: {e}")
        return None


def fetch_weather_data_for_last_month(city: str):
    """
    Fetches weather data for the last month (from DATE constant until today) for a given city.
    """
    end_date = datetime.strptime(DATE, "%Y-%m-%d")
    start_date = end_date - timedelta(days=30)  # Start date is 30 days before today

    for single_date in (start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1)):
        date_str = single_date.strftime("%Y-%m-%d")
        print(f"Fetching weather data for {city} on {date_str}...")
        weather_data = fetch_weather_data(city, date_str)
        if weather_data:
            print(f"SUCCESS: Weather data fetched for {city} on {date_str}.")
        else:
            print(f"WARNING: Failed to fetch weather data for {city} on {date_str}.")


if __name__ == "__main__":
    city_name = "London"  # Example city
    fetch_weather_data_for_last_month(city_name)