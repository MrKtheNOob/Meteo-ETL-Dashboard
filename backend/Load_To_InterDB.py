from datetime import datetime
from typing import Dict, List, Tuple
from models import (
    Condition,
    CurrentWeatherData,
    LocationData,
    CurrentWeatherApiResponse,  # Updated to use CurrentWeatherApiResponse
)


def bulk_insert_data(cursor, all_api_responses: List[CurrentWeatherApiResponse]):
    """
    Performs bulk inserts for locations, conditions, and weather data.
    Assumes tables are erased before insertion and there's a 1:1 location-weather record.
    """
    # Step 0: Extract data and maintain order for locations and their associated weather
    locations_ordered: List[LocationData] = []
    conditions_to_insert: Dict[Condition, None] = {} # Still need unique conditions
    weather_data_raw: List[CurrentWeatherData] = [] # Maintain order corresponding to locations_ordered

    for api_response in all_api_responses:
        locations_ordered.append(api_response.location)
        conditions_to_insert[api_response.current.condition] = None
        weather_data_raw.append(api_response.current)

    # --- Step 1: Bulk Insert Conditions ---
    # Prepare data for conditions_meteo bulk insert
    # This can be done first as condition codes are predefined and independent.
    conditions_data = [
        (cond.code, cond.text)
        for cond in conditions_to_insert.keys()
    ]

    if conditions_data:
        query_insert_conditions = """
        INSERT IGNORE INTO conditions_meteo (code_condition, texte_condition)
        VALUES (%s, %s)
        """
        try:
            print(f"INFO: Attempting to bulk insert {len(conditions_data)} conditions...")
            cursor.executemany(query_insert_conditions, conditions_data)
            print("SUCCESS: Bulk insert of conditions completed.")
        except Exception as e:
            print(f"ERROR: Failed to bulk insert conditions - {e}")
            raise

    # --- Step 2: Bulk Insert Locations ---
    # Prepare data for lieux bulk insert
    lieux_to_insert = [
        (loc.name, loc.region, loc.country)
        for loc in locations_ordered
    ]

    location_id_map: Dict[Tuple[str, str, str], int] = {} # To store the mapping from data to generated ID
    if lieux_to_insert:
        query_insert_lieux = """
        INSERT IGNORE INTO lieux (nom, region, pays)
        VALUES (%s, %s, %s)
        """
        try:
            print(f"INFO: Attempting to bulk insert {len(lieux_to_insert)} locations...")
            cursor.executemany(query_insert_lieux, lieux_to_insert)

            # Retrieve the starting ID of the first inserted row
            # and infer subsequent IDs.
            # This relies on AUTO_INCREMENT allocating sequential IDs for a single executemany call.
            first_id = cursor.lastrowid
            if first_id is None: # Should not happen if rows were inserted
                raise RuntimeError("Failed to get lastrowid after lieux bulk insert.")

            for i, loc in enumerate(locations_ordered):
                location_id_map[(loc.name, loc.region, loc.country)] = first_id + i

            print(f"SUCCESS: Bulk insert of locations completed. Generated IDs from {first_id} onwards.")
        except Exception as e:
            print(f"ERROR: Failed to bulk insert locations - {e}")
            raise

    # --- Step 3: Bulk Insert Weather Data ---
    # Prepare data for donnees_meteo bulk insert
    donnees_meteo_to_insert = []
    for i, weather_record in enumerate(weather_data_raw):
        # We use the original location object from locations_ordered to find its ID
        original_location = locations_ordered[i]
        location_tuple = (original_location.name, original_location.region, original_location.country)
        location_id = location_id_map.get(location_tuple)

        # This check is still useful as a safeguard, though less likely to be triggered
        # if the assumptions (fresh tables, 1:1, sequential IDs) hold.
        if location_id is None:
            print(f"WARNING: Could not find ID for location {location_tuple}. Skipping weather data for this entry.")
            continue

        datetime_obj = datetime.strptime(weather_record.last_updated, "%Y-%m-%d %H:%M")

        donnees_meteo_to_insert.append(
            (
                location_id,
                datetime_obj,
                weather_record.temp_c,
                weather_record.wind_kph,
                weather_record.wind_degree,
                weather_record.wind_dir,
                weather_record.pressure_mb,
                weather_record.precip_mm,
                weather_record.humidity,
                weather_record.cloud,
                weather_record.vis_km,
                weather_record.uv,
                weather_record.gust_kph,
                weather_record.condition.code,
            )
        )

    if donnees_meteo_to_insert:
        query_insert_weather_data = """
        INSERT IGNORE INTO donnees_meteo (
            id_lieu, datetime_observation, temperature_celsius, vent_kph, vent_degre,
            direction_vent, pression_millibars, precipitation_mm, humidite_pourcentage,
            nuages_pourcentage, visibilite_km, indice_uv, rafales_kph, code_condition
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            print(f"INFO: Attempting to bulk insert {len(donnees_meteo_to_insert)} weather observations...")
            cursor.executemany(query_insert_weather_data, donnees_meteo_to_insert)
            print("SUCCESS: Bulk insert of weather observations completed.")
        except Exception as e:
            print(f"ERROR: Failed to bulk insert weather data - {e}")
            raise

    # Final commit for the entire operation
    try:
        cursor.connection.commit()
        print("SUCCESS: All bulk inserts committed successfully.")
    except Exception as e:
        print(f"ERROR: Failed to commit transaction - {e}")
        cursor.connection.rollback()
        raise