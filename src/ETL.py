from dotenv import load_dotenv
from multiprocessing import Pool, cpu_count
from Load import insert_location, insert_weather_data
from Extract import WEATHERAPI_KEY, fetch_weather_data
from cleanup import cleanup_and_recreate_db
from utils import get_db_connection
from models import HistoricalWeatherApiResponse
from datetime import datetime, timedelta
from typing import Optional

load_dotenv()

# --- ETL Configuration ---
UEMOA_CITIES: list[str] = [
    "Africa/Cotonou", "Africa/Porto-Novo", "Africa/Bafata",  # Bénin
    "Africa/Ouagadougou", "Africa/Bobo-Dioulasso",           # Burkina Faso
    "Africa/Abidjan", "Africa/Yamoussoukro", "Africa/Bouake",  # Côte d'Ivoire
    "Africa/Bissau", "Africa/Gabu", "Africa/Bolama",         # Guinée-Bissau
    "Africa/Bamako", "Africa/Sikasso", "Africa/Segou",       # Mali
    "Africa/Niamey", "Africa/Zinder", "Africa/Maradi",       # Niger
    "Africa/Dakar", "Africa/Thiès", "Africa/Saint-Louis",    # Sénégal
    "Africa/Lomé", "Africa/Sokodé", "Africa/Kara"            # Togo
]

def process_city_data(city: str) -> None:
    """
    Processes weather data for a single city for the last month.
    """
    conn = get_db_connection()
    if not conn:
        print(f"ERROR: Failed to establish database connection for {city}.")
        return

    cursor = conn.cursor()
    try:
        end_date: datetime = datetime.now()
        start_date: datetime = end_date - timedelta(days=30)

        for single_date in (start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1)):
            date_str: str = single_date.strftime("%Y-%m-%d")
            print(f"Fetching weather data for {city} on {date_str}...")
            weather_data_raw: Optional[HistoricalWeatherApiResponse] = fetch_weather_data(city, date_str)
            if not weather_data_raw:
                print(f"WARNING: Skipping {city} on {date_str} due to API fetch error.")
                continue

            try:
                # Parse the raw weather data into the HistoricalWeatherApiResponse model
                weather_data: HistoricalWeatherApiResponse = HistoricalWeatherApiResponse.model_validate(weather_data_raw.model_dump())

                # Insert location data
                location_id: Optional[int] = insert_location(cursor, weather_data.location)
                if not location_id:
                    print(f"ERROR: Failed to insert location data for {city}. Skipping...")
                    continue

                # Insert weather data
                insert_weather_data(cursor, location_id, weather_data)
                conn.commit()
                print(f"SUCCESS: Data for {city} on {date_str} committed to the database.")
            except Exception as e:
                print(f"ERROR: Rolling back changes for {city} on {date_str} due to error: {e}")
                conn.rollback()
    except Exception as e:
        print(f"ERROR: An unexpected error occurred for {city}: {e}")
    finally:
        cursor.close()
        conn.close()
        print(f"INFO: Finished processing data for {city}.")

def run_etl() -> None:
    """Main ETL process using multiprocessing."""
    if not WEATHERAPI_KEY:
        print("ERROR: WEATHERAPI_KEY is not set. Please provide your WeatherAPI.com API key.")
        return

    conn = get_db_connection()
    if not conn:
        print("ERROR: Failed to establish database connection.")
        return

    cursor = conn.cursor()
    try:
        # Clean up and recreate the database schema
        cleanup_and_recreate_db(cursor)
        print("INFO: Database successfully cleaned up and recreated.")
    except Exception as e:
        print(f"ERROR: Failed to clean up and recreate the database schema: {e}")
        return
    finally:
        cursor.close()
        conn.close()

    # Use multiprocessing to process cities in parallel
    print("INFO: Starting multiprocessing for city data extraction.")
    with Pool(cpu_count()) as pool:
        pool.map(process_city_data, UEMOA_CITIES)

    print("\nINFO: ETL process completed.")

if __name__ == "__main__":
    run_etl()
