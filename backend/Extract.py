import asyncio
import os
from typing import List
from dotenv import load_dotenv
from utils import UEMOA_CITIES
from models import CurrentWeatherApiResponse
import aiohttp

async def call_api(city: str, output: List[CurrentWeatherApiResponse]):
    WEATHERAPI_KEY = os.getenv("API_KEY")
    if not WEATHERAPI_KEY:
        print("ERROR: WEATHERAPI_KEY is not set.")
        return

    api_url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={city}&aqi=no"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                data = await response.json()
                weather_data = CurrentWeatherApiResponse.parse_obj(data)
                output.append(weather_data)
                print("Fetched data for", city)
    except Exception as e:
        print(f"Error for {city}: {e}")

async def get_weather_data(output: List[CurrentWeatherApiResponse]):
    tasks = [call_api(city, output) for city in UEMOA_CITIES]
    await asyncio.gather(*tasks)

def extract() -> List[CurrentWeatherApiResponse]:
    load_dotenv()
    output = []
    asyncio.run(get_weather_data(output))
    print(f"Fetched {len(output)}/{len(UEMOA_CITIES)} cities")
    return output

if __name__ == "__main__":
    extract()