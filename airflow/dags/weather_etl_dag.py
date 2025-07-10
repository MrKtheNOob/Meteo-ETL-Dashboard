from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
import pendulum
from datetime import datetime, timedelta
import sys
import os

# Add src directory to Python path for custom module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import ETL modules
from Extract import WEATHERAPI_KEY, fetch_current_weather_data
from Load_To_InterDB import insert_location, insert_weather_data
from transform import transform_load_to_warehouse
from cleanup import cleanup_and_recreate_db
from utils import get_db_connection
from models import CurrentWeatherApiResponse
from typing import Optional

# List of cities for ETL
UEMOA_CITIES = [
    "Africa/Porto-Novo", "Africa/Bafata",
    "Africa/Ouagadougou", "Africa/Bobo-Dioulasso",
    "Africa/Abidjan", "Africa/Yamoussoukro", "Africa/Bouake",
    "Africa/Bissau", "Africa/Gabu", "Africa/Bolama",
    "Africa/Bamako", "Africa/Sikasso", "Africa/Segou",
    "Africa/Niamey", "Africa/Zinder", "Africa/Maradi",
    "Africa/Dakar", "Africa/Thiès", "Africa/Saint-Louis",
    "Africa/Lomé", "Africa/Sokodé", "Africa/Kara"
]

def log_etl_process(process_name: str, status: str, start_time: datetime, end_time: datetime = None, error_message: str = None, rows_processed: int = None) -> None:
    conn = get_db_connection("meteo")
    if not conn:
        print("ERROR: Failed to connect to DB for ETL logging.")
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO etl_logs (process_name, status, start_time, end_time, error_message, rows_processed)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (process_name, status, start_time, end_time, error_message, rows_processed))
        conn.commit()
        print(f"INFO: Logged ETL process '{process_name}' with status '{status}'.")
    except Exception as e:
        print(f"ERROR: ETL log insert failed - {e}")
    finally:
        cursor.close()
        conn.close()

def process_city_data(city: str) -> None:
    start_time = datetime.now()
    conn = get_db_connection("meteo")
    if not conn:
        print(f"ERROR: DB connection failed for {city}")
        log_etl_process("process_city_data", "failed", start_time, error_message=f"DB connect failed for {city}")
        return
    cursor = conn.cursor()
    rows_processed = 0
    try:
        print(f"Fetching weather for {city}...")
        weather_data_raw: Optional[CurrentWeatherApiResponse] = fetch_current_weather_data(city)
        if not weather_data_raw:
            print(f"WARNING: Skipping {city}, API fetch failed.")
            log_etl_process("process_city_data", "failed", start_time, error_message=f"API fetch failed for {city}")
            return
        try:
            location_id: Optional[int] = insert_location(cursor, weather_data_raw.location)
            if not location_id:
                print(f"ERROR: Location insert failed for {city}")
                log_etl_process("process_city_data", "failed", start_time, error_message=f"Location insert failed for {city}")
                return
            insert_weather_data(cursor, location_id, weather_data_raw)
            conn.commit()
            rows_processed += 1
            print(f"SUCCESS: Weather data for {city} committed.")
        except Exception as e:
            print(f"ERROR: Rollback for {city} due to {e}")
            conn.rollback()
            log_etl_process("process_city_data", "failed", start_time, error_message=str(e))
    except Exception as e:
        print(f"ERROR: Unexpected error for {city}: {e}")
        log_etl_process("process_city_data", "failed", start_time, error_message=str(e))
    finally:
        cursor.close()
        conn.close()
        log_etl_process("process_city_data", "success", start_time, datetime.now(), rows_processed=rows_processed)
        print(f"INFO: Finished processing {city}.")

def validate_api_key():
    if not WEATHERAPI_KEY:
        raise ValueError("WEATHERAPI_KEY not set. Provide your WeatherAPI key.")
    print("INFO: WeatherAPI key validated.")
    return True

def cleanup_database():
    print("INFO: Starting DB cleanup...")
    conn = get_db_connection("meteo")
    if conn is None:
        raise Exception("Failed DB connection for cleanup.")
    try:
        cleanup_and_recreate_db(conn.cursor())
        print("INFO: DB cleanup done.")
    finally:
        conn.close()

def extract_and_load_data():
    print("INFO: Starting extraction/loading...")
    start_time = datetime.now()
    import time
    for city in UEMOA_CITIES:
        process_city_data(city)
        time.sleep(0.5)  # To avoid API rate limit
    print("INFO: Extraction/loading done.")
    log_etl_process("extract_and_load", "success", start_time, datetime.now())

def transform_and_load_to_warehouse():
    print("INFO: Starting transform/load to warehouse...")
    start_time = datetime.now()
    try:
        transform_load_to_warehouse()
        log_etl_process("transfer_data_to_warehouse", "success", start_time, datetime.now())
        print("INFO: Transform/load done.")
    except Exception as e:
        print(f"ERROR: Transform/load failed - {e}")
        log_etl_process("transfer_data_to_warehouse", "failed", start_time, error_message=str(e))
        raise

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': pendulum.now("UTC").subtract(days=1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    "weather_etl_dag",
    default_args=default_args,
    description="ETL pipeline for weather data from UEMOA cities",
    schedule="0 */1 * * *",  # every 6 hours, use 'schedule' for Airflow 2.8+
    catchup=False,
    tags=["weather", "etl", "uemoa"],
)

start_task = EmptyOperator(task_id='start', dag=dag)
validate_api_task = PythonOperator(task_id='validate_api_key', python_callable=validate_api_key, dag=dag)
cleanup_db_task = PythonOperator(task_id='cleanup_database', python_callable=cleanup_database, dag=dag)
extract_load_task = PythonOperator(task_id='extract_and_load_data', python_callable=extract_and_load_data, dag=dag)
transform_warehouse_task = PythonOperator(task_id='transform_and_load_to_warehouse', python_callable=transform_and_load_to_warehouse, dag=dag)
end_task = EmptyOperator(task_id='end', dag=dag)

start_task >> validate_api_task >> cleanup_db_task >> extract_load_task >> transform_warehouse_task >> end_task
