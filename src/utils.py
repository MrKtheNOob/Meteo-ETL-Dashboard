import os
from dotenv import load_dotenv
from pymysql import Connection
import pymysql
from pymysql import cursors

# Ordre de suppression
TABLE_DROP_ORDER = [
    "conditions_meteo", 
    "donnees_meteo", 
    "lieux"
    ]

# Ordre de création
TABLE_CREATE_STATEMENTS = [
    """
    CREATE TABLE lieux (
        id_lieu INT AUTO_INCREMENT PRIMARY KEY, 
        nom VARCHAR(255) NOT NULL,              
        region VARCHAR(255),                    
        pays VARCHAR(255) NOT NULL             
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
    """,
]


def connect_mysql() -> Connection:
    """Establishes and returns a database connection using hardcoded parameters."""
    load_dotenv()
    timeout = 10
    connection = pymysql.connect(
        charset="utf8mb4",
        connect_timeout=timeout,
        cursorclass=cursors.DictCursor,
        db=os.getenv("DB_NAME", ""),
        host=os.getenv("HOST", ""),
        password=os.getenv("PASSWORD", ""),
        read_timeout=timeout,
        port=int(os.getenv("PORT", "")),
        user=os.getenv("DB_USER", ""),
        write_timeout=timeout,
    )
    print("Database connection established successfully.")
    return connection


def get_db_connection():
    """Wrapper for connect_mysql to maintain compatibility with existing code."""
    try:
        conn = connect_mysql()
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None
