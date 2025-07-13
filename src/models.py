from datetime import datetime
from pydantic import BaseModel
from typing import Optional


# Weather Condition 
class Condition(BaseModel):
    text: str
    code: int
    class Config:
        frozen=True

# Location Data 
class LocationData(BaseModel):
    name: str
    region: str
    country: str
    class Config:
        frozen = True # Makes instances immutable and hashable

    
# Current Weather Data (matching the 'donnees_meteo' table for DB storage)
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

    
    class Config:
        frozen = True # Makes instances immutable and hashable


# Overall Current Weather API Response
class CurrentWeatherApiResponse(BaseModel):
    location: LocationData  
    current: CurrentWeatherData
    class Config:
        frozen = True


# -- Models for the Warehouse DB

# DimTemps Model
class DimTemps(BaseModel):
    date: str  # Matches 'date' in DimTemps (DATE type)
    annee: int  # Matches 'annee' in DimTemps
    mois: int  # Matches 'mois' in DimTemps
    jour: int  # Matches 'jour' in DimTemps
    heure: int  # Matches 'heure' in DimTemps
    minute: int  # Matches 'minute' in DimTemps
    jour_semaine: str  # Matches 'jour_semaine' in DimTemps
    nom_mois: str  # Matches 'nom_mois' in DimTemps


# DimLieux Model
class DimLieux(BaseModel):
    nom_ville: str  # Matches 'nom_ville' in DimLieux
    region: Optional[str]  # Matches 'region' in DimLieux
    pays: str  # Matches 'pays' in DimLieux


# DimConditionsMeteo Model
class DimConditionsMeteo(BaseModel):
    code_condition: int  # Matches 'code_condition' in DimConditionsMeteo
    texte_condition: str  # Matches 'texte_condition' in DimConditionsMeteo


# FaitDonneesMeteo Model
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


