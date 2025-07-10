from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional


# 1. Weather Condition (reusable for both location and hourly data)
class Condition(BaseModel):
    text: str
    code: int
    # icon: Optional[HttpUrl] = None # Icon URL, present in source JSON, but only 'code' and 'text' are typically stored in DB

# 2. Location Data (now matching the *simplified* 'lieux' table for DB storage)
# Fields like 'lat', 'lon', 'tz_id', 'localtime_epoch', 'localtime' are present in the source JSON,
# but are explicitly excluded from this Pydantic model to reflect the simplified 'lieux' DB table
class LocationData(BaseModel):
    name: str
    region: str
    country: str

# 3. Hourly Historical Weather Data (now matching the *simplified* 'donnees_meteo' table for DB storage)
# Fields like 'is_day', 'chance_of_rain', and others (e.g., feelslike_c, precip_in)
# are present in the source JSON but are explicitly excluded from this Pydantic model
# to align with the simplified 'donnees_meteo' DB table.
class HourlyHistoricalData(BaseModel):
    time: str # Raw time string from JSON (e.g., "YYYY-MM-DD HH:MM") - will be converted to datetime_observation in DB
    temp_c: float # Maps to temperature_celsius in DB
    condition: Condition # Nested Pydantic model for weather condition (code will be FK in DB)
    wind_kph: float # Maps to vent_kph in DB
    wind_degree: int # Maps to vent_degre in DB
    wind_dir: str # Maps to direction_vent in DB
    pressure_mb: float # Maps to pression_millibars in DB
    precip_mm: float # Maps to precipitation_mm in DB
    humidity: int # Maps to humidite_pourcentage in DB
    cloud: int # Maps to nuages_pourcentage in DB
    vis_km: float # Maps to visibilite_km in DB
    gust_kph: float # Maps to rafales_kph in DB
    uv: float # Maps to indice_uv in DB

    # Fields from JSON that are explicitly NOT included here (and will be ignored during parsing)
    # because they are not in the 'donnees_meteo' MySQL schema:
    # is_day, chance_of_rain, temp_f, wind_mph, pressure_in, precip_in, snow_cm,
    # feelslike_c, feelslike_f, windchill_c, windchill_f,
    # heatindex_c, heatindex_f, dewpoint_c, dewpoint_f,
    # will_it_rain, will_it_snow, chance_of_snow, vis_miles.


# 4. Forecast Day Container (to extract hourly data from each day's forecast)
# This model represents the structure of a single 'forecastday' object in the API response.
class ForecastDayHistorical(BaseModel):
    date: str # Date of the forecast day (e.g., "YYYY-MM-DD")
    hour: List[HourlyHistoricalData] # List of hourly data for this day, using the simplified HourlyHistoricalData model

# 5. Overall Historical Weather API Response
# This model represents the top-level structure of the API response.
class HistoricalWeatherApiResponse(BaseModel):
    location: LocationData # The simplified LocationData model
    forecast: dict # Use dict to access 'forecastday' as it's a dynamic key in the validator
    
    # Custom validator to extract forecastday directly from the nested 'forecast' dictionary.
    # This method is crucial because the 'forecast' field in the API response is a dictionary
    # that contains 'forecastday' as one of its keys.
    @classmethod
    def parse_obj(cls, data: dict):
        forecastday_data = data.get("forecast", {}).get("forecastday", [])
        # Create a list of ForecastDayHistorical instances from the extracted data
        parsed_forecastday = [ForecastDayHistorical.parse_obj(day_data) for day_data in forecastday_data]
        
        # Return a new instance of HistoricalWeatherApiResponse, passing the parsed location
        # and the list of parsed ForecastDayHistorical objects as part of the 'forecast' dictionary.
        return cls(location=LocationData.parse_obj(data["location"]), forecast={"forecastday": parsed_forecastday})

# -- Models for the Warehouse DB

# 6. DimTemps Model
class DimTemps(BaseModel):
    date: str  # Matches 'date' in DimTemps (DATE type)
    annee: int  # Matches 'annee' in DimTemps
    mois: int  # Matches 'mois' in DimTemps
    jour: int  # Matches 'jour' in DimTemps
    heure: int  # Matches 'heure' in DimTemps
    minute: int  # Matches 'minute' in DimTemps
    jour_semaine: str  # Matches 'jour_semaine' in DimTemps
    nom_mois: str  # Matches 'nom_mois' in DimTemps


# 7. DimLieux Model
class DimLieux(BaseModel):
    nom_ville: str  # Matches 'nom_ville' in DimLieux
    region: Optional[str]  # Matches 'region' in DimLieux
    pays: str  # Matches 'pays' in DimLieux


# 8. DimConditionsMeteo Model
class DimConditionsMeteo(BaseModel):
    code_condition: int  # Matches 'code_condition' in DimConditionsMeteo
    texte_condition: str  # Matches 'texte_condition' in DimConditionsMeteo


# 9. FaitDonneesMeteo Model
class FaitDonneesMeteo(BaseModel):
    id_dim_lieu_fk: int  # Matches 'id_dim_lieu_fk' in FaitDonneesMeteo (Foreign key to DimLieux.id_dim_lieu)
    date_fk: datetime  # Matches 'datetime_fk' in FaitDonneesMeteo (Foreign key to DimTemps.date)
    id_dim_condition_fk: int  # Matches 'id_dim_condition_fk' in FaitDonneesMeteo (Foreign key to DimConditionsMeteo.id_dim_condition)
    temperature_celsius: float  # Matches 'temperature_celsius' in FaitDonneesMeteo
    vent_kph: float  # Matches 'vent_kph' in FaitDonneesMeteo
    vent_degre: int  # Matches 'vent_degre' in FaitDonneesMeteo
    direction_vent: str  # Matches 'direction_vent' in FaitDonneesMeteo
    pression_millibars: float  # Matches 'pression_millibars' in FaitDonneesMeteo
    precipitation_mm: float  # Matches 'precipitation_mm' in FaitDonneesMeteo
    humidite_pourcentage: int  # Matches 'humidite_pourcentage' in FaitDonneesMeteo
    nuages_pourcentage: int  # Matches 'nuages_pourcentage' in FaitDonneesMeteo
    visibilite_km: float  # Matches 'visibilite_km' in FaitDonneesMeteo
    indice_uv: float  # Matches 'indice_uv' in FaitDonneesMeteo
    rafales_kph: float  # Matches 'rafales_kph' in FaitDonneesMeteo


# 10. Current Weather Data (matching the 'donnees_meteo' table for DB storage)
class CurrentWeatherData(BaseModel):
    last_updated: str  # Maps to datetime_observation in DB
    temp_c: float  # Maps to temperature_celsius in DB
    condition: Condition  # Nested Pydantic model for weather condition (code will be FK in DB)
    wind_kph: float  # Maps to vent_kph in DB
    wind_degree: int  # Maps to vent_degre in DB
    wind_dir: str  # Maps to direction_vent in DB
    pressure_mb: float  # Maps to pression_millibars in DB
    precip_mm: float  # Maps to precipitation_mm in DB
    humidity: int  # Maps to humidite_pourcentage in DB
    cloud: int  # Maps to nuages_pourcentage in DB
    vis_km: float  # Maps to visibilite_km in DB
    uv: float  # Maps to indice_uv in DB
    gust_kph: float  # Maps to rafales_kph in DB


# 11. Overall Current Weather API Response
class CurrentWeatherApiResponse(BaseModel):
    location: LocationData  # The simplified LocationData model
    current: CurrentWeatherData  # The CurrentWeatherData model

