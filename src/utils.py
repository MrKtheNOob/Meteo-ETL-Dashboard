import os
from dotenv import load_dotenv
from pymysql import Connection
import pymysql
from pymysql import cursors


UEMOA_CITIES = [
	# Benin
	"Africa/Porto-Novo", "Africa/Cotonou", "Africa/Parakou", "Africa/Abomey-Calavi", "Africa/Djougou",
	"Africa/Bohicon", "Africa/Kandi", "Africa/Natitingou", "Africa/Ouidah", "Africa/Lokossa",
	"Africa/Savalou", "Africa/Sakete", "Africa/Dassa-Zoume", "Africa/Malanville", "Africa/Pobe",

	# Burkina Faso
	"Africa/Ouagadougou", "Africa/Bobo-Dioulasso", "Africa/Koudougou", "Africa/Ouahigouya",
	"Africa/Banfora", "Africa/Fada_Ngourma", "Africa/Dedougou", "Africa/Nouna",
	"Africa/Dori", "Africa/Manga", "Africa/Tenkodogo", "Africa/Ziniare",

	# Côte d'Ivoire
	"Africa/Abidjan", "Africa/Yamoussoukro", "Africa/Bouake", "Africa/Daloa", "Africa/Korhogo",
	"Africa/Man", "Africa/San-Pedro", "Africa/Gagnoa", "Africa/Divo", "Africa/Anyama",
	"Africa/Adzope", "Africa/Abengourou", "Africa/Grand-Bassam", "Africa/Aboisso", "Africa/Seguela",

	# Guinee-Bissau
	"Africa/Bissau", "Africa/Bafata", "Africa/Gabu", "Africa/Canchungo", "Africa/Cacheu",
	"Africa/Bolama", "Africa/Bissora", "Africa/Farim", "Africa/Catio", "Africa/Buba",

	# Mali
	"Africa/Bamako", "Africa/Sikasso", "Africa/Segou", "Africa/Mopti", "Africa/Kayes",
	"Africa/Koutiala", "Africa/Gao", "Africa/Kati", "Africa/San", "Africa/Timbuktu",
	"Africa/Niono", "Africa/Bougouni", "Africa/Kidal", "Africa/Tessalit",

	# Niger
	"Africa/Niamey", "Africa/Zinder", "Africa/Maradi", "Africa/Tahoua", "Africa/Agadez",
	"Africa/Arlit", "Africa/Dosso", "Africa/Diffa", "Africa/Birni-N'Konni", "Africa/Gaya",
	"Africa/Tillaberi", "Africa/Tera",

	# Senegal
	"Africa/Dakar", "Africa/Pikine", "Africa/Touba", "Africa/Thies", "Africa/Saint-Louis",
	"Africa/Kaolack", "Africa/Ziguinchor", "Africa/Mbour", "Africa/Rufisque", "Africa/Diourbel",
	"Africa/Tambacounda", "Africa/Louga", "Africa/Kolda", "Africa/Fatick", "Africa/Kaffrine",
	"Africa/Sedhiou", "Africa/Kedougou", "Africa/Matam",

	# Togo
	"Africa/Lome", "Africa/Sokode", "Africa/Kara", "Africa/Kpalime", "Africa/Atakpame",
	"Africa/Dapaong", "Africa/Tsevie", "Africa/Aneho", "Africa/Mango", "Africa/Bassar",
	"Africa/Tchamba", "Africa/Niamtougou", "Africa/Notse", "Africa/Vogan",
]
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

