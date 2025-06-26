from datetime import datetime
from typing import Optional
from models import (
    Condition,
    LocationData,
    HistoricalWeatherApiResponse,
)


def insert_location(cursor, location: LocationData) -> Optional[int]:
    """
    Inserts a unique location into the 'lieux' table if it doesn't exist.
    Returns the ID of the location.
    """
    query_insert = """
    INSERT IGNORE INTO lieux (nom, region, pays)
    VALUES (%s, %s, %s)
    """
    query_select = """
    SELECT id_lieu FROM lieux WHERE nom = %s AND region = %s AND pays = %s
    """
    try:
        # Check if the location already exists
        cursor.execute(query_select, (location.name, location.region, location.country))
        result = cursor.fetchone()
        if result:
            return result["id_lieu"]  # Return the existing location ID

        # Insert the location if it doesn't exist
        cursor.execute(query_insert, (location.name, location.region, location.country))
        if cursor.rowcount == 1:
            return cursor.lastrowid  # Return the newly inserted location ID
        return None
    except Exception as e:
        print(f"Error inserting location {location.name}: {e}")
        return None


def insert_condition(cursor, condition: Condition) -> None:
    """
    Inserts a unique weather condition into the 'conditions_meteo' table if it doesn't exist.
    """
    query = """
    INSERT IGNORE INTO conditions_meteo (code_condition, texte_condition)
    VALUES (%s, %s)
    """
    try:
        cursor.execute(query, (condition.code, condition.text))
    except Exception as e:
        print(f"Error inserting condition {condition.text}: {e}")


def insert_weather_data(cursor, location_id: int, weather_data: HistoricalWeatherApiResponse) -> None:
    """
    Inserts weather data into the 'donnees_meteo' table.
    """
    try:
        for forecast_day in weather_data.forecast["forecastday"]:
            for hourly_data in forecast_day.hour:
                insert_condition(cursor, hourly_data.condition)
                query_hourly_weather = """
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
                    query_hourly_weather,
                    (
                        location_id,
                        datetime.strptime(hourly_data.time, "%Y-%m-%d %H:%M"),
                        hourly_data.temp_c,
                        hourly_data.wind_kph,
                        hourly_data.wind_degree,
                        hourly_data.wind_dir,
                        hourly_data.pressure_mb,
                        hourly_data.precip_mm,
                        hourly_data.humidity,
                        hourly_data.cloud,
                        hourly_data.vis_km,
                        hourly_data.uv,
                        hourly_data.gust_kph,
                        hourly_data.condition.code,
                    ),
                )
    except Exception as e:
        print(f"Error processing weather data: {e}")
        raise
