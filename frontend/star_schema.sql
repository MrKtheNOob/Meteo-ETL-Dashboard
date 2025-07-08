-- Disable foreign key checks to allow dropping tables in any order
SET FOREIGN_KEY_CHECKS = 0;

-- Drop all tables
DROP TABLE IF EXISTS FaitDonneesMeteo;
DROP TABLE IF EXISTS DimConditionsMeteo;
DROP TABLE IF EXISTS DimLieux;
DROP TABLE IF EXISTS DimTemps;

-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Recreate tables with fixes

-- DimTemps Table
CREATE TABLE DimTemps (
    id_dim_temps INT AUTO_INCREMENT PRIMARY KEY, -- New Primary Key
    date DATE NOT NULL,                  
    annee INT NOT NULL,                          --
    mois INT NOT NULL,                           --
    jour INT NOT NULL,                           --
    heure INT NOT NULL,                          --
    minute INT NOT NULL,                         --
    jour_semaine VARCHAR(20) NOT NULL,           --
    nom_mois VARCHAR(20) NOT NULL                --
);

-- DimLieux Table
CREATE TABLE DimLieux (
    id_dim_lieu INT AUTO_INCREMENT PRIMARY KEY, -- Auto-increment for unique IDs
    nom_ville VARCHAR(255) NOT NULL,            --
    region VARCHAR(255),                        --
    pays VARCHAR(255) NOT NULL                  --
);

-- DimConditionsMeteo Table
CREATE TABLE DimConditionsMeteo (
    id_dim_condition INT AUTO_INCREMENT PRIMARY KEY, -- Auto-increment for unique IDs
    code_condition INT NOT NULL,                     --
    texte_condition VARCHAR(255) NOT NULL UNIQUE     --
);

-- FaitDonneesMeteo Table
CREATE TABLE FaitDonneesMeteo (
    id_observation_horaire INT AUTO_INCREMENT PRIMARY KEY, -- Auto-increment for unique IDs
    id_dim_lieu_fk INT NOT NULL,                         --
    id_dim_temps_fk INT NOT NULL,                        -- Changed to reference id_dim_temps
    id_dim_condition_fk INT NOT NULL,                    --

    temperature_celsius DECIMAL(5,2) NOT NULL,           --
    vent_kph DECIMAL(5,2) NOT NULL,                      --
    vent_degre INT NOT NULL,                             --
    direction_vent VARCHAR(10) NOT NULL,                 --
    pression_millibars DECIMAL(7,2) NOT NULL,            --
    precipitation_mm DECIMAL(5,2) NOT NULL,              --
    humidite_pourcentage INT NOT NULL,                   --
    nuages_pourcentage INT NOT NULL,                     --
    visibilite_km DECIMAL(5,2) NOT NULL,                 --
    indice_uv DECIMAL(4,1) NOT NULL,                     --
    rafales_kph DECIMAL(5,2) NOT NULL,                   --

    UNIQUE (id_dim_lieu_fk, id_dim_temps_fk),            -- Unique constraint updated

    FOREIGN KEY (id_dim_lieu_fk) REFERENCES DimLieux(id_dim_lieu),           --
    FOREIGN KEY (id_dim_temps_fk) REFERENCES DimTemps(id_dim_temps),         -- Foreign key references new primary key
    FOREIGN KEY (id_dim_condition_fk) REFERENCES DimConditionsMeteo(id_dim_condition) --
);