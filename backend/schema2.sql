-- Schéma Historique de la Base de Données Météo (MySQL DDL)

-- Création de la base de données
CREATE DATABASE IF NOT EXISTS meteo;
USE meteo;

-- Suppression des tables existantes pour éviter les conflits
SET FOREIGN_KEY_CHECKS = 0; -- Désactiver les vérifications des clés étrangères
DROP TABLE IF EXISTS donnees_meteo;
DROP TABLE IF EXISTS conditions_meteo;
DROP TABLE IF EXISTS lieux;
SET FOREIGN_KEY_CHECKS = 1; -- Réactiver les vérifications des clés étrangères

-- Table: lieux
CREATE TABLE lieux (
    id_lieu INT AUTO_INCREMENT PRIMARY KEY, -- Identifiant unique du lieu
    nom VARCHAR(255) NOT NULL,              -- Nom du lieu (ex: Dakar)
    region VARCHAR(255),                    -- Région du lieu (ex: Dakar)
    pays VARCHAR(255) NOT NULL,             -- Pays du lieu (ex: Sénégal)

    UNIQUE (nom, region, pays)              -- Contrainte d'unicité sur les colonnes 'nom', 'region', et 'pays'
);

-- Table: conditions_meteo
CREATE TABLE conditions_meteo (
    code_condition INT PRIMARY KEY,         -- Code unique de la condition météorologique
    texte_condition VARCHAR(255) NOT NULL UNIQUE -- Description textuelle de la condition
);

-- Table: donnees_meteo
CREATE TABLE donnees_meteo (
    id_observation_horaire INT AUTO_INCREMENT PRIMARY KEY, -- Identifiant unique de l'observation horaire
    id_lieu INT NOT NULL,                                 -- Clé étrangère vers la table 'lieux'
    datetime_observation DATETIME NOT NULL,                      -- Date et heure précises de l'observation
    temperature_celsius DECIMAL(5,2) NOT NULL,           -- Température observée en degrés Celsius
    vent_kph DECIMAL(5,2) NOT NULL,                      -- Vitesse du vent en kilomètres par heure
    vent_degre INT NOT NULL,                             -- Direction du vent en degrés (0-360)
    direction_vent VARCHAR(10) NOT NULL,                 -- Direction cardinale du vent (ex: "NW")
    pression_millibars DECIMAL(7,2) NOT NULL,            -- Pression atmosphérique en millibars
    precipitation_mm DECIMAL(5,2) NOT NULL,              -- Précipitations en millimètres
    humidite_pourcentage INT NOT NULL,                   -- Humidité en pourcentage
    nuages_pourcentage INT NOT NULL,                     -- Couverture nuageuse en pourcentage
    visibilite_km DECIMAL(5,2) NOT NULL,                 -- Visibilité en kilomètres
    indice_uv DECIMAL(4,1) NOT NULL,                     -- Indice UV
    rafales_kph DECIMAL(5,2) NOT NULL,                   -- Vitesse des rafales de vent en kilomètres par heure
    code_condition INT NOT NULL,                         -- Clé étrangère vers la table 'conditions_meteo'

    UNIQUE (id_lieu, date_observation), -- Assure une seule observation par lieu et par horodatage précis
    FOREIGN KEY (id_lieu) REFERENCES lieux(id_lieu),
    FOREIGN KEY (code_condition) REFERENCES conditions_meteo(code_condition)
);

-- Création des index pour optimiser les requêtes
CREATE INDEX idx_dmhh_id_lieu ON donnees_meteo(id_lieu);
CREATE INDEX idx_datetime_observation ON donnees_meteo(date_observation);
