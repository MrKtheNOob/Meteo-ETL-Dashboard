from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
import pendulum
from datetime import datetime, timedelta
import sys
import os

# Add src directory to Python path for custom module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..','backend'))

# Import ETL modules
from backend.Extract import extract
from backend.Load_To_InterDB import bulk_insert_data
from backend.transform import transform_load_to_warehouse
from backend.cleanup import cleanup_and_recreate_db
from backend.utils import get_db_connection
from backend.models import CurrentWeatherApiResponse
from typing import List, Optional

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

def extract_and_load_to_source():
    print("INFO: Starting extraction/loading...")
    start_time = datetime.now()
    log_etl_process("run_etl", "running", start_time)
    try:
        raw_city_data:List[CurrentWeatherApiResponse]=extract()
    except Exception as e:
        print("Error extracting API data :",e)
        log_etl_process("run_etl", "failed", start_time, error_message=f"Error extracting API data :{e}")
        return
    print("SUCCESS: API Extraction successful")
    conn = get_db_connection("meteo")
    bulk_insert_data(conn.cursor(),raw_city_data)

def transform_and_load_to_warehouse():
    print("INFO: Starting transform/load to warehouse...")
    start_time = datetime.now()
    try:
        transform_load_to_warehouse()  # Hook to transfer data from intermediate DB to warehouse
        log_etl_process("transfer_data_to_warehouse", "success", start_time, datetime.now())
    except Exception as e:
        print(f"ERROR: Data transfer to warehouse failed - {e}")
        log_etl_process("transfer_data_to_warehouse", "failed", start_time, error_message=str(e))

    log_etl_process("run_etl", "success", start_time, datetime.now())
    print("\nINFO: ETL process completed.")

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
cleanup_db_task = PythonOperator(task_id='cleanup_database', python_callable=cleanup_database, dag=dag)
extract_load_task = PythonOperator(task_id='extract_and_load_to_source', python_callable=extract_and_load_to_source, dag=dag)
transform_warehouse_task = PythonOperator(task_id='transform_and_load_to_warehouse', python_callable=transform_and_load_to_warehouse, dag=dag)
end_task = EmptyOperator(task_id='end', dag=dag)

start_task >> cleanup_db_task >> extract_load_task >> transform_warehouse_task >> end_task
