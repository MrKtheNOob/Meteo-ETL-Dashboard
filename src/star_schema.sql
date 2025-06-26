-- CREATE DATABASE meteo_warehouse;
-- USE meteo_warehouse;

CREATE TABLE DimTemps (
    datetime_key DATETIME PRIMARY KEY,
    annee INT NOT NULL,
    mois INT NOT NULL,
    jour INT NOT NULL,
    heure INT NOT NULL,
    minute INT NOT NULL,
    jour_semaine VARCHAR(20) NOT NULL,
    nom_mois VARCHAR(20) NOT NULL
);

CREATE TABLE DimLieux (
    id_dim_lieu INT AUTO_INCREMENT PRIMARY KEY,
    nom_ville VARCHAR(255) NOT NULL,
    region VARCHAR(255),
    pays VARCHAR(255) NOT NULL
);
CREATE TABLE DimConditionsMeteo (
    id_dim_condition INT PRIMARY KEY,
    code_condition INT ,
    texte_condition VARCHAR(255) NOT NULL UNIQUE
);

-- Fact table that references datetime correctly
CREATE TABLE FaitDonneesMeteo (
    id_observation_horaire INT AUTO_INCREMENT PRIMARY KEY,
    id_dim_lieu_fk INT NOT NULL,
    datetime_fk DATETIME NOT NULL,
    id_dim_condition_fk INT NOT NULL,

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

    UNIQUE (id_dim_lieu_fk, datetime_fk),

    FOREIGN KEY (id_dim_lieu_fk) REFERENCES DimLieux(id_dim_lieu),
    FOREIGN KEY (datetime_fk) REFERENCES DimTemps(datetime_key),
    FOREIGN KEY (id_dim_condition_fk) REFERENCES DimConditionsMeteo(id_dim_condition)
);
