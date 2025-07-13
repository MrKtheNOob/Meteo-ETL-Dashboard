from flask import Flask, jsonify , render_template, send_from_directory
from flask_caching import Cache
from ETL import run_etl
from utils import get_db_connection
import threading
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the path for the templates folder. This points to the ../dist directory relative to the api.py location.
templates_folder_path = os.path.abspath("../dist")

# Raise an error if the templates folder does not exist to prevent issues during deployment.
if not os.path.exists(templates_folder_path):
    raise ValueError(f"Templates folder path '{templates_folder_path}' does not exist.")

# Initialize the Flask application, setting the template_folder to serve frontend files.
app = Flask(__name__, template_folder=templates_folder_path)

# Configure Flask-Caching for API responses.
app.config['CACHE_TYPE'] = 'SimpleCache'
cache = Cache(app)

def _fetch_all_weather_data():
    """
    Fetch all weather data from the database.
    """
    conn = get_db_connection("meteo_warehouse")
    if not conn:
        return None, {"error": "Failed to connect to the database"}

    cursor = conn.cursor()
    try:
        # Query to get all weather data with joins
        query = """
        SELECT 
            f.id_observation_horaire,
            f.id_dim_lieu_fk,
            f.id_dim_temps_fk,
            f.id_dim_condition_fk,
            f.temperature_celsius,
            f.vent_kph,
            f.vent_degre,
            f.direction_vent,
            f.pression_millibars,
            f.precipitation_mm,
            f.humidite_pourcentage,
            f.nuages_pourcentage,
            f.visibilite_km,
            f.indice_uv,
            f.rafales_kph,
            l.id_dim_lieu,
            l.nom_ville,
            l.region,
            l.pays,
            t.id_dim_temps,
            t.date,
            t.annee,
            t.mois,
            t.jour,
            t.heure,
            t.minute,
            t.jour_semaine,
            t.nom_mois,
            c.id_dim_condition,
            c.code_condition,
            c.texte_condition
        FROM FaitDonneesMeteo f
        JOIN DimLieux l ON f.id_dim_lieu_fk = l.id_dim_lieu
        JOIN DimTemps t ON f.id_dim_temps_fk = t.id_dim_temps
        JOIN DimConditionsMeteo c ON f.id_dim_condition_fk = c.id_dim_condition
        ORDER BY t.date DESC, t.heure DESC limit 1000
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries matching the data.json format
        result = []
        for row in rows:
            result.append({
                'id_observation_horaire': row['id_observation_horaire'],
                'id_dim_lieu_fk': row['id_dim_lieu_fk'],
                'id_dim_temps_fk': row['id_dim_temps_fk'],
                'id_dim_condition_fk': row['id_dim_condition_fk'],
                'temperature_celsius': float(row['temperature_celsius']),
                'vent_kph': float(row['vent_kph']),
                'vent_degre': row['vent_degre'],
                'direction_vent': row['direction_vent'],
                'pression_millibars': float(row['pression_millibars']),
                'precipitation_mm': float(row['precipitation_mm']),
                'humidite_pourcentage': row['humidite_pourcentage'],
                'nuages_pourcentage': row['nuages_pourcentage'],
                'visibilite_km': float(row['visibilite_km']),
                'indice_uv': float(row['indice_uv']),
                'rafales_kph': float(row['rafales_kph']),
                'lieu': {
                    'id_dim_lieu': row['id_dim_lieu'],
                    'nom_ville': row['nom_ville'],
                    'region': row['region'],
                    'pays': row['pays']
                },
                'temps': {
                    'id_dim_temps': row['id_dim_temps'],
                    'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']),
                    'annee': row['annee'],
                    'mois': row['mois'],
                    'jour': row['jour'],
                    'heure': row['heure'],
                    'minute': row['minute'],
                    'jour_semaine': row['jour_semaine'],
                    'nom_mois': row['nom_mois']
                },
                'condition': {
                    'id_dim_condition': row['id_dim_condition'],
                    'code_condition': row['code_condition'],
                    'texte_condition': row['texte_condition']
                }
            })
        
        return result, None
        
    except Exception as e:
        return None, {"error": "Failed to fetch weather data", "details": str(e)}
    finally:
        cursor.close()
        conn.close()

def run_etl_with_status():
    """
    Runs the ETL (Extract, Transform, Load) process in a separate thread.
    Updates the ETL status in the cache (e.g., 'running', 'finished', 'error').
    """
    cache.set('etl_status', 'running')
    try:
        run_etl()
        cache.set('etl_status', 'finished')
    except Exception as e:
        # If an error occurs during ETL, store the error message in the cache.
        cache.set('etl_status', f"error: {str(e)}")

@app.route('/trigger-etl', methods=['GET'])
def trigger_etl():
    """
    API endpoint to trigger the ETL process.
    It checks if an ETL process is already running to avoid multiple concurrent executions.
    """
    etl_status = cache.get('etl_status')
    if etl_status == 'running':
        return jsonify({"message": "ETL process is already running."}), 409

    # Start the ETL process in a new thread so the API call does not block.
    thread = threading.Thread(target=run_etl_with_status)
    thread.start()
    return jsonify({"message": "ETL process triggered successfully."}), 202

@app.route('/etl-status', methods=['GET'])
def get_etl_status():
    """
    API endpoint to get the current status of the ETL process.
    """
    status = cache.get('etl_status', 'idle')  # Default to 'idle' if no status is found
    return jsonify({"status": status}), 200

@app.route('/api/weather/all', methods=['GET'])
def get_all_weather_data():
    """
    API endpoint to fetch all weather data.
    This endpoint returns all weather data for client-side filtering.
    """
    rows, error = _fetch_all_weather_data()
    if error:
        return jsonify(error), 500
    return jsonify(rows), 200

@app.route('/api/weather/locations', methods=['GET'])
def get_locations():
    """
    API endpoint to fetch available locations from the database.
    """
    conn = get_db_connection("meteo_warehouse")
    if not conn:
        return jsonify({"error": "Failed to connect to the database"}), 500

    cursor = conn.cursor()
    try:
        query = "SELECT DISTINCT nom_ville FROM DimLieux ORDER BY nom_ville"
        cursor.execute(query)
        rows = [row['nom_ville'] for row in cursor.fetchall()]
        return jsonify(rows), 200
    except Exception as e:
        # Handle exceptions during location fetching.
        return jsonify({"error": "Failed to fetch locations", "details": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def serve_index():
    """
    Serve the index.html file for the root URL.
    This ensures that navigating to the base URL loads the frontend application.
    """
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    """
    Serve any other static files (like JS, CSS, images, etc.) from the frontend build directory.
    This route catches all other paths not explicitly handled by other API routes.
    """
    return send_from_directory(str(app.template_folder), filename)

if __name__ == '__main__':
    # Run the Flask app with debug mode enabled for development.
    # In production, consider using a WSGI server like Gunicorn or uWSGI.
    app.run(debug=True, port=int(os.getenv("PORT", 25451)))
