from flask import Flask, jsonify
from flask_caching import Cache
from ETL import run_etl
from utils import get_db_connection
import threading

app = Flask(__name__)

# Configure Flask-Caching
app.config['CACHE_TYPE'] = 'SimpleCache'
cache = Cache(app)

def run_etl_with_status():
    """
    Runs the ETL process and updates the status in the cache.
    """
    cache.set('etl_status', 'running')
    try:
        run_etl()
        cache.set('etl_status', 'finished')
    except Exception as e:
        cache.set('etl_status', f"error: {str(e)}")

@app.route('/trigger-etl', methods=['GET'])
def trigger_etl():
    """
    Endpoint to trigger the ETL process.
    """
    etl_status = cache.get('etl_status')
    if etl_status == 'running':
        return jsonify({"message": "ETL process is already running."}), 409

    # Run the ETL process in a separate thread to avoid blocking the API
    thread = threading.Thread(target=run_etl_with_status)
    thread.start()
    return jsonify({"message": "ETL process started successfully."}), 200

@app.route('/etl-status', methods=['GET'])
def etl_status_endpoint():
    """
    Endpoint to check the status of the ETL process.
    """
    etl_status = cache.get('etl_status') or 'idle'
    return jsonify({"status": etl_status}), 200

@app.route('/etl-logs', methods=['GET'])
def get_etl_logs():
    """
    Endpoint to fetch ETL logs from the database and serve them as JSON.
    """
    conn = get_db_connection("meteo")  # Connect to the intermediate database
    if not conn:
        return jsonify({"error": "Failed to connect to the database"}), 500

    cursor = conn.cursor()
    try:
        query = "SELECT * FROM etl_logs ORDER BY created_at DESC"
        cursor.execute(query)
        logs = cursor.fetchall()
        return jsonify(logs), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch logs", "details": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)