# Extract.py
import os
from typing import Optional
from dotenv import load_dotenv
import requests
from models import CurrentWeatherApiResponse

load_dotenv()

WEATHERAPI_KEY = os.getenv("API_KEY")


def fetch_current_weather_data(city: str) -> Optional[CurrentWeatherApiResponse]:
    """
    Fetches current weather data from the WeatherAPI for a given city.
    """
    if not WEATHERAPI_KEY:
        print("ERROR: WEATHERAPI_KEY is not set.")
        return None

    api_url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={city}&aqi=no"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        # Validate and parse the response using the Pydantic model
        weather_data = CurrentWeatherApiResponse.parse_obj(data)
        return weather_data
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed for {city}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching data for {city}: {e}")
        return None