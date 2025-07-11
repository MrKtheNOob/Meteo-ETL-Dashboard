# Pipeline ETL Météo et Entrepôt de Données

## Introduction

Ce projet a mis en œuvre un **pipeline ETL** pour collecter, traiter et stocker des données météorologiques de l'API WeatherAPI.com dans un entrepôt de données. Un tableau de bord a également été développé pour la visualisation et la validation des données.

-----

## Approche et Architecture

Un **système ETL personnalisé basé sur Python** a été choisi pour sa flexibilité et son contrôle, permettant une gestion précise de chaque étape du flux de données. Le pipeline a été conçu pour :

  * **Récupérer séquentiellement** les données via l'API WeatherAPI.com.
  * **Traiter et nettoyer** les données brutes.
  * **Insérer** les données dans une base de données source relationnelle, puis dans un entrepôt de données.
  * **Gérer les limitations de l'API** et les contraintes de ressources (CPU/RAM) via des pauses (`time.sleep()`).

-----

## Conception des Schémas de Base de Données

### Schéma de la Base de Données Source

Un **schéma relationnel** a été créé pour la base source, optimisé pour les **opérations transactionnelles** et l'intégrité des données brutes.

### Schéma de l'Entrepôt de Données (Schéma en Étoile)

Un **schéma en étoile** a été implémenté pour l'entrepôt de données, optimisé pour l'**analyse et le reporting**. Il comprend une **table de faits centrale** (`FaitDonneesMeteo`) et des **tables de dimensions** (`DimLieux`, `DimConditionsMeteo`, `DimTemps`), facilitant l'exploration et l'analyse des données.

-----

## Processus ETL et Transformations

Les données extraites de l'API ont été transformées pour passer d'un format transactionnel à une structure dénormalisée adaptée au schéma en étoile. Cela a impliqué :

  * **Parsing et validation des JSON** via Pydantic.
  * **Mappage des attributs** aux tables de faits et de dimensions.
  * **Décomposition des horodatages** pour la dimension temps.
  * **Insertion des données** via `pymysql`, avec gestion explicite des transactions pour la cohérence.

-----

## API de Données Météo

Une API Flask a été développée pour exposer les données de l'entrepôt et gérer le processus ETL :

  * `/trigger-etl` (GET) : Déclenche le processus ETL en arrière-plan.
  * `/etl-status` (GET) : Donne le statut de l'ETL.
  * `/api/weather/all` (GET) : Récupère toutes les données météo.
  * `/api/weather/locations` (GET) : Liste les villes disponibles.
  * `/` et `/<path:filename>` (GET) : Servent le frontend et les fichiers statiques.

**Flask-Caching** a été utilisé pour optimiser les réponses, et le traitement ETL s'exécute dans un **thread séparé** pour éviter de bloquer l'API.

-----

## Tableau de Bord et Validation

Un tableau de bord interactif a été développé avec **React** pour interroger l'API Flask, permettant une exploration dynamique et une validation des données.

🔗 Tableau de bord en ligne : [https://meteo-etl-dashboard.onrender.com/](https://www.google.com/search?q=https://meteo-etl-dashboard.onrender.com/)

-----

## Intégration Additionnelle (Airflow)

Après la finalisation du pipeline Python, un prototype local **Airflow** a été intégré pour démontrer la capacité à orchestrer des flux de données complexes en entreprise. L'**entrée principale de l'ETL est `ETL.py`** et l'**API est servie par `api.py`**.

-----

## Configuration de Airflow

Le répertoire Airflow est structuré comme suit :

```
. ├── airflow
│ ├── airflow.cfg
│ ├── airflow.db
│ ├── dags
│ │ └── weather_etl_dag.py
│ ├── docker-compose.yml
│ └── dockerfile
```

### ✅ Prérequis

  * **Docker** et **Docker Compose** installés.
  * Connaissances de base du terminal.

### Contenu du Dossier Expliqué

  * `airflow.cfg` : Fichier de configuration Airflow.
  * `airflow.db` : Base de données SQLite locale pour les métadonnées Airflow.
  * `dags/` : Contient vos DAGs (ex: `weather_etl_dag.py`).
  * `docker-compose.yml` : Définit les services Docker pour Airflow.
  * `dockerfile` : Permet de créer une image Docker personnalisée (ex: pour installer des packages).

### Créer l'Image Docker Airflow

Dans le répertoire `airflow` :

```bash
cd airflow
docker build -t custom-airflow:latest -f dockerfile .
```

-----

### ⚙️ Vérifier / Modifier `docker-compose.yml`

Assurez-vous que `docker-compose.yml` utilise l'image personnalisée que vous venez de créer :

```yaml
version: '3'
services:
  airflow:
    image: custom-airflow:latest
    environment:
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db
    volumes:
      - ./dags:/opt/airflow/dags
      - ./airflow.cfg:/opt/airflow/airflow.cfg
      - ./airflow.db:/opt/airflow/airflow.db
    ports:
      - "8080:8080"
    command: webserver
```

-----

### Démarrer Airflow

```bash
docker-compose up
```

Ceci exécute le serveur web Airflow à l'adresse [http://localhost:8080](https://www.google.com/search?q=http://localhost:8080).

-----

### Initialiser la Base de Données (uniquement lors de la première exécution)

Si c'est votre première exécution :

```bash
docker-compose run airflow airflow db init
```

Puis redémarrez :

```bash
docker-compose up
```

-----

### Accéder à l'Interface Utilisateur d'Airflow

Ouvrez [http://localhost:8080](https://www.google.com/search?q=http://localhost:8080).
Identifiants par défaut : `airflow` / `airflow` (si inchangé).

-----

### Vérifiez votre DAG

Dans l'interface utilisateur, vous devriez voir `weather_etl_dag.py` listé. Activez-le et déclenchez-le si nécessaire.

-----

### Arrêter Airflow

```bash
docker-compose down
```

-----

### 💬 Remarques

  * L'utilisation de **SQLite** est idéale pour les tests locaux. Pour la production, utilisez **Postgres** ou **MySQL**.
  * Votre `airflow.db` est monté en volume, garantissant la **persistance des données** après le redémarrage du conteneur.
  * Personnalisez le `dockerfile` pour installer des packages Python ou d'autres outils nécessaires (ex: `RUN pip install requests`).

-----

### ✅ Résumé

1️⃣ **Construire votre image** 🧱
2️⃣ **Vérifier** que `docker-compose.yml` pointe vers elle 🎯
3️⃣ **Exécuter** `docker-compose up` 🚀
4️⃣ **Accéder** à l'interface utilisateur à `localhost:8080` 🌐
