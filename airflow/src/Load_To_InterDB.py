from datetime import datetime
from typing import Optional
from models import (
    Condition,
    LocationData,
    CurrentWeatherApiResponse,  # Updated to use CurrentWeatherApiResponse
)


def insert_location(cursor, location: LocationData) -> Optional[int]:
    """
    Inserts a unique location into the 'lieux' table.
    Returns the ID of the location.
    """
    query_insert = """
    INSERT INTO lieux (nom, region, pays)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE id_lieu = LAST_INSERT_ID(id_lieu)
    """
    try:
        print(f"INFO: Inserting location '{location.name}' into the database...")
        cursor.execute(query_insert, (location.name, location.region, location.country))
        cursor.connection.commit()
        print(f"SUCCESS: Location '{location.name}' inserted with ID {cursor.lastrowid}.")
        return cursor.lastrowid
    except Exception as e:
        print(f"ERROR: Failed to insert location '{location.name}' - {e}")
        raise


def insert_condition(cursor, condition: Condition) -> None:
    """
    Inserts a unique weather condition into the 'conditions_meteo' table if it doesn't exist.
    """
    query = """
    INSERT INTO conditions_meteo (code_condition, texte_condition)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE texte_condition = VALUES(texte_condition)
    """
    try:
        print(f"INFO: Inserting condition '{condition.text}' with code {condition.code}...")
        cursor.execute(query, (condition.code, condition.text))
        cursor.connection.commit()
        print(f"SUCCESS: Condition '{condition.text}' inserted or updated successfully.")
    except Exception as e:
        print(f"ERROR: Failed to insert condition '{condition.text}' - {e}")
        raise


def insert_weather_data(cursor, location_id: int, weather_data: CurrentWeatherApiResponse) -> None:
    """
    Inserts current weather data into the 'donnees_meteo' table.
    """
    try:
        print(f"INFO: Processing current weather data for location ID {location_id}...")
        # Insert condition
        insert_condition(cursor, weather_data.current.condition)

        query_current_weather = """
        INSERT INTO donnees_meteo (
            id_lieu, datetime_observation, temperature_celsius, vent_kph, vent_degre,
            direction_vent, pression_millibars, precipitation_mm, humidite_pourcentage,
            nuages_pourcentage, visibilite_km, indice_uv, rafales_kph, code_condition
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            temperature_celsius = VALUES(temperature_celsius),
            vent_kph = VALUES(vent_kph),
            vent_degre = VALUES(vent_degre),
            direction_vent = VALUES(direction_vent),
            pression_millibars = VALUES(pression_millibars),
            precipitation_mm = VALUES(precipitation_mm),
            humidite_pourcentage = VALUES(humidite_pourcentage),
            nuages_pourcentage = VALUES(nuages_pourcentage),
            visibilite_km = VALUES(visibilite_km),
            indice_uv = VALUES(indice_uv),
            rafales_kph = VALUES(rafales_kph),
            code_condition = VALUES(code_condition)
        """
        cursor.execute(
            query_current_weather,
            (
                location_id,
                datetime.strptime(weather_data.current.last_updated, "%Y-%m-%d %H:%M"),
                weather_data.current.temp_c,
                weather_data.current.wind_kph,
                weather_data.current.wind_degree,
                weather_data.current.wind_dir,
                weather_data.current.pressure_mb,
                weather_data.current.precip_mm,
                weather_data.current.humidity,
                weather_data.current.cloud,
                weather_data.current.vis_km,
                weather_data.current.uv,
                weather_data.current.gust_kph,
                weather_data.current.condition.code,
            ),
        )
        cursor.connection.commit()
        print(f"SUCCESS: Current weather data for location ID {location_id} inserted successfully.")
    except Exception as e:
        print(f"ERROR: Failed to process current weather data for location ID {location_id} - {e}")
        raise
