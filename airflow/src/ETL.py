import time
from dotenv import load_dotenv
from datetime import datetime
from transform import transform_load_to_warehouse
from Extract import WEATHERAPI_KEY, fetch_current_weather_data
from Load_To_InterDB import insert_location, insert_weather_data
from cleanup import cleanup_and_recreate_db
from utils import get_db_connection
from models import CurrentWeatherApiResponse
from typing import Optional

load_dotenv()
# "Africa/Cotonou",
# --- ETL Configuration ---
UEMOA_CITIES = [
     "Africa/Porto-Novo", "Africa/Bafata",  # Bénin
    "Africa/Ouagadougou", "Africa/Bobo-Dioulasso",           # Burkina Faso
    "Africa/Abidjan", "Africa/Yamoussoukro", "Africa/Bouake",  # Côte d'Ivoire
    "Africa/Bissau", "Africa/Gabu", "Africa/Bolama",         # Guinée-Bissau
    "Africa/Bamako", "Africa/Sikasso", "Africa/Segou",       # Mali
    "Africa/Niamey", "Africa/Zinder", "Africa/Maradi",       # Niger
    "Africa/Dakar", "Africa/Thiès", "Africa/Saint-Louis",    # Sénégal
    "Africa/Lomé", "Africa/Sokodé", "Africa/Kara"            # Togo
]

def log_etl_process(process_name: str, status: str, start_time: datetime, end_time: Optional[datetime] = None, error_message: Optional[str] = None, rows_processed: Optional[int] = None) -> None:
    """
    Logs ETL process details into the etl_logs table in the meteo database.
    """
    conn = get_db_connection("meteo")  # Connect to the intermediate database
    if not conn:
        print("ERROR: Failed to establish database connection for logging.")
        return

    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO etl_logs (process_name, status, start_time, end_time, error_message, rows_processed)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (process_name, status, start_time, end_time, error_message, rows_processed))
        conn.commit()
        print(f"INFO: Logged ETL process '{process_name}' with status '{status}'.")
    except Exception as e:
        print(f"ERROR: Failed to log ETL process '{process_name}' - {e}")
    finally:
        cursor.close()
        conn.close()


def process_city_data(city: str) -> None:
    """
    Processes current weather data for a single city sequentially.
    """
    start_time = datetime.now()
    conn = get_db_connection("meteo")  # Connect to the intermediate database
    if not conn:
        print(f"ERROR: Failed to establish database connection for {city}.")
        log_etl_process("process_city_data", "failed", start_time, error_message=f"Failed to connect to database for {city}")
        return

    cursor = conn.cursor()
    rows_processed = 0
    try:
        print(f"Fetching current weather data for {city}...")
        weather_data_raw: Optional[CurrentWeatherApiResponse] = fetch_current_weather_data(city)
        if not weather_data_raw:
            print(f"WARNING: Skipping {city} due to API fetch error.")
            log_etl_process("process_city_data", "failed", start_time, error_message=f"API fetch error for {city}")
            return

        try:
            print(f"INFO: Inserting location data for {city}...")
            location_id: Optional[int] = insert_location(cursor, weather_data_raw.location)
            if not location_id:
                print(f"ERROR: Failed to insert location data for {city}. Skipping...")
                log_etl_process("process_city_data", "failed", start_time, error_message=f"Failed to insert location data for {city}")
                return

            print(f"INFO: Inserting current weather data for location ID {location_id}...")
            insert_weather_data(cursor, location_id, weather_data_raw)
            conn.commit()
            rows_processed += 1
            print(f"SUCCESS: Current weather data for {city} committed to the database.")
        except Exception as e:
            print(f"ERROR: Rolling back changes for {city} due to error: {e}")
            conn.rollback()
            log_etl_process("process_city_data", "failed", start_time, error_message=str(e))
    except Exception as e:
        print(f"ERROR: An unexpected error occurred for {city}: {e}")
        log_etl_process("process_city_data", "failed", start_time, error_message=str(e))
    finally:
        cursor.close()
        conn.close()
        log_etl_process("process_city_data", "success", start_time, datetime.now(), rows_processed=rows_processed)
        print(f"INFO: Finished processing data for {city}.")
        

def run_etl() -> None:
    """Main ETL process running sequentially."""
    start_time = datetime.now()
    log_etl_process("run_etl", "running", start_time)
    if not WEATHERAPI_KEY:
        print("ERROR: WEATHERAPI_KEY is not set. Please provide your WeatherAPI.com API key.")
        log_etl_process("run_etl", "failed", start_time, error_message="WEATHERAPI_KEY is not set")
        return

    print("INFO: Starting database cleanup...")
    conn = get_db_connection("meteo")
    if conn is None:
        print("ERROR: Failed to establish database connection for cleanup.")
        return

    cleanup_and_recreate_db(conn.cursor())
    conn.close()

    print("INFO: Starting data extraction and loading into intermediate database...")
    
    for city in UEMOA_CITIES:
        process_city_data(city)
        time.sleep(0.5)

    print("INFO: Starting data transfer to warehouse...")
    try:
        transform_load_to_warehouse()  # Hook to transfer data from intermediate DB to warehouse
        log_etl_process("transfer_data_to_warehouse", "success", start_time, datetime.now())
    except Exception as e:
        print(f"ERROR: Data transfer to warehouse failed - {e}")
        log_etl_process("transfer_data_to_warehouse", "failed", start_time, error_message=str(e))

    log_etl_process("run_etl", "success", start_time, datetime.now())
    print("\nINFO: ETL process completed.")

if __name__ == "__main__":
    run_etl()


