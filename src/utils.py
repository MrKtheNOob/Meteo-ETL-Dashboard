import os
from dotenv import load_dotenv
from pymysql import Connection
import pymysql
from pymysql import cursors
from datetime import datetime

from models import DimTemps

# Ordre de suppression
TABLE_DROP_ORDER = [
    "donnees_meteo",
    "conditions_meteo",
    "lieux"
]

# Ordre de création
TABLE_CREATE_STATEMENTS = [
    """
    CREATE TABLE lieux (
        id_lieu INT AUTO_INCREMENT PRIMARY KEY, 
        nom VARCHAR(255) NOT NULL,              
        region VARCHAR(255),                    
        pays VARCHAR(255) NOT NULL,             

        UNIQUE (nom, region, pays)              
    );
    """,
    """
    CREATE TABLE conditions_meteo (
        code_condition INT PRIMARY KEY,         
        texte_condition VARCHAR(255) NOT NULL UNIQUE
    );
    """,
    """
    CREATE TABLE donnees_meteo (
        id_observation_horaire INT AUTO_INCREMENT PRIMARY KEY, 
        id_lieu INT NOT NULL,                                 
        datetime_observation DATETIME NOT NULL,                      
        temperature_celsius DECIMAL(5,2) NOT NULL,           
        vent_kph DECIMAL(5,2) NOT NULL,                      
        vent_degre INT NOT NULL,                             
        direction_vent VARCHAR(10) NOT NULL,                 
        pression_millibars DECIMAL(7,2) NOT NULL,            
        precipitation_mm DECIMAL(5,2) NOT NULL,              
        humidite_pourcentage INT NOT NULL,                   
        nuages_pourcentage INT NOT NULL,                     
        visibilite_km DECIMAL(5,2) NOT NULL,                 
        indice_uv DECIMAL(4,1) NOT NULL,                     
        rafales_kph DECIMAL(5,2) NOT NULL,                   
        code_condition INT NOT NULL,                         

        UNIQUE (id_lieu, datetime_observation), 
        FOREIGN KEY (id_lieu) REFERENCES lieux(id_lieu),
        FOREIGN KEY (code_condition) REFERENCES conditions_meteo(code_condition)
    );
    """
]


def connect_mysql(db_name: str) -> Connection:
    """
    Establishes and returns a database connection using the given database name.
    """
    load_dotenv()
    timeout = 10
    connection = pymysql.connect(
        charset="utf8mb4",
        connect_timeout=timeout,
        cursorclass=cursors.DictCursor,
        db=db_name,
        host=os.getenv("HOST", ""),
        password=os.getenv("PASSWORD", ""),
        read_timeout=timeout,
        port=int(os.getenv("DB_PORT", "")),
        user=os.getenv("DB_USER", ""),
        write_timeout=timeout,
    )
    print(f"Database connection to '{db_name}' established successfully.")
    return connection


def get_db_connection(db_name: str) -> Connection|None:
    """
    Wrapper for connect_mysql to establish a connection to the specified database.
    """
    try:
        conn = connect_mysql(db_name)
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to MySQL database '{db_name}': {e}")
        return None


def transfer_dim_temps(cursor_source, cursor_target) -> None:
    """
    Transfers data from the intermediate database to the DimTemps table in the warehouse.
    """
    query_source = """
    SELECT DISTINCT datetime_observation
    FROM donnees_meteo
    """
    query_target = """
    INSERT INTO DimTemps (datetime_key, annee, mois, jour, heure, minute, jour_semaine, nom_mois)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE datetime_key = VALUES(datetime_key)
    """
    cursor_source.execute(query_source)
    for row in cursor_source.fetchall():
        datetime_key = row["datetime_observation"]

        # Ensure datetime_key is a datetime object
        if isinstance(datetime_key, str):
            dt = datetime.strptime(datetime_key, "%Y-%m-%d %H:%M:%S")
        elif isinstance(datetime_key, datetime):
            dt = datetime_key
        else:
            print(f"WARNING: Unexpected type for datetime_key: {type(datetime_key)}")
            continue

        dim_temps = DimTemps(
            date=dt.strftime("%Y-%m-%d"),
            annee=dt.year,
            mois=dt.month,
            jour=dt.day,
            heure=dt.hour,
            minute=dt.minute,
            jour_semaine=dt.strftime("%A"),
            nom_mois=dt.strftime("%B"),
        )
        cursor_target.execute(
            query_target,
            (
                dim_temps.date,
                dim_temps.annee,
                dim_temps.mois,
                dim_temps.jour,
                dim_temps.heure,
                dim_temps.minute,
                dim_temps.jour_semaine,
                dim_temps.nom_mois,
            ),
        )
