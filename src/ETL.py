from dotenv import load_dotenv
from datetime import datetime
from InterDB_To_Warehouse import transform_load_to_warehouse
from Extract import extract
from Load_To_InterDB import bulk_insert_data
from cleanup import cleanup_and_recreate_db
from utils import get_db_connection
from models import CurrentWeatherApiResponse
from typing import List, Optional

load_dotenv()


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

        

def run_etl() -> None:
    """Main ETL process running sequentially."""
    start_time = datetime.now()
    log_etl_process("run_etl", "running", start_time)
    try:
        raw_city_data:List[CurrentWeatherApiResponse]=extract()
    except Exception as e:
        print("Error extracting API data :",e)
        log_etl_process("run_etl", "failed", start_time, error_message=f"Error extracting API data :{e}")
        return
    print("SUCCESS: API Extraction successful")

    print("INFO: Starting database cleanup...")
    conn = get_db_connection("meteo")
    if conn is None:
        print("ERROR: Failed to establish database connection for cleanup.")
        return

    cleanup_and_recreate_db(conn.cursor())

    bulk_insert_data(conn.cursor(),raw_city_data)

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


