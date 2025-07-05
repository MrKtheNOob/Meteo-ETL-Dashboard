# Rapport de Projet : Pipeline ETL Météo et Entrepôt de Données

## Introduction

Durant ce projet, un pipeline ETL (Extract, Transform, Load) entièrement fonctionnel a été conçu et mis en œuvre pour collecter, traiter et stocker des données météorologiques provenant de l'API [WeatherAPI.com](https://www.weatherapi.com/) dans un entrepôt de données centralisé.  
En parallèle, un tableau de bord a été développé pour visualiser les données et valider l'intégrité et l'exploitabilité du pipeline.

## Approche et Architecture

En raison des contraintes de compatibilité et d'installation avec les outils ETL GUI lourds (par exemple, Talend, SSIS), un système ETL personnalisé basé sur Python a été choisi. Cette décision a permis un meilleur contrôle, une itération rapide et une compréhension approfondie de chaque étape du flux de données.

Le pipeline a été conçu pour :

- Récupérer séquentiellement les données pour chaque ville via l'API WeatherAPI.com.
- Traiter et nettoyer les données brutes.
- Les insérer initialement dans une base de données source relationnelle.
- Gérer les limitations de l'API et les contraintes CPU des instances gratuites grâce à un cadencement intelligent (`time.sleep()`).

## Conception des Schémas de Base de Données

### Schéma de la Base de Données Source

Un schéma relationnel a été créé pour la base source, destinée à la capture initiale des données météorologiques actuelles et des prévisions. Ce schéma est optimisé pour les opérations transactionnelles, minimisant la redondance et assurant l'intégrité des données.

### Schéma de l'Entrepôt de Données (Schéma en Étoile)

Un schéma en étoile a été choisi pour l'entrepôt de données, optimisé pour l'analyse et le reporting. Il est composé :

- D'une table de faits centrale (`FaitDonneesMeteo`) pour les mesures météorologiques horaires.
- De tables de dimensions connectées (`DimLieux`, `DimConditionsMeteo`, `DimTemps`).

Ce choix facilite l'exploration des données et améliore les performances analytiques.

## Processus ETL et Algorithmes de Transformation

Les données brutes extraites de l'API ont été transformées pour passer d’un format transactionnel à une structure dénormalisée adaptée au schéma en étoile. Les étapes comprenaient :

- Parsing et validation des JSON via Pydantic.
- Mappage des attributs aux tables de faits et de dimensions.
- Décomposition des horodatages (année, mois, jour, heure, minute) pour la dimension temps.
- Insertion des données transformées dans les tables via `pymysql`, en gérant explicitement les transactions pour assurer la cohérence.

## API de Données Météo

Une API a été développée en Flask pour exposer les données de l'entrepôt :

- `/trigger-etl` (GET) : Déclenche le processus ETL en arrière-plan.
- `/etl-status` (GET) : Statut actuel du processus ETL (en cours, terminé, erreur).
- `/api/weather/all` (GET) : Toutes les données météo disponibles.
- `/api/weather/locations` (GET) : Liste des villes disponibles.
- `/` (GET) : Sert le frontend (index.html).
- `/<path:filename>` (GET) : Sert les fichiers statiques (JS, CSS, etc.).

L'utilisation de Flask-Caching a permis d’optimiser les réponses, et le traitement ETL est exécuté dans un thread séparé pour ne pas bloquer les requêtes API.

## Cron-Jobs

La logique ETL a été encapsulée pour être déclenchée par des tâches planifiées (cron jobs), notamment via [cron-job.org](https://cron-job.org/) pour appeler `/trigger-etl`.

## Tableau de Bord et Validation

Un tableau de bord interactif a été développé avec React et des librairies de visualisation modernes. Il interroge directement l’API Flask et permet une exploration dynamique et une validation des données.  

🔗 **Tableau de bord en ligne** : [https://meteo-etl-dashboard.onrender.com/](https://meteo-etl-dashboard.onrender.com/)

## Défis Clés

- **Limitations des outils** : Incapacité d’utiliser des ETL GUI (Talend, SSIS), nécessitant une approche codée.
- **Contraintes de ressources** : Limites CPU/RAM strictes, nécessitant des optimisations pour éviter les plantages.
- **Contraintes DB** : Problèmes de clés et relations, résolus par des insertions séquentielles et gestion explicite des transactions.

## Intégration Additionnelle (Airflow)

Après la finalisation du pipeline Python, un prototype local Airflow a été intégré pour démontrer la compréhension des orchestrateurs utilisés en entreprise.

## Leçons Apprises

- Conception complète d'un pipeline ETL, orchestration, gestion des erreurs et ressources.
- Compréhension de l’équilibre entre simplicité, maintenabilité et conformité aux standards.
- Optimisation et déploiement sous contraintes strictes.
- Pratique du débogage et amélioration itérative basée sur les retours du système.

## Conclusion

Ce projet a permis d’atteindre les objectifs fondamentaux d’ETL et d’entrepôt de données tout en fournissant une expérience réaliste et orientée production.  
Il a renforcé les compétences techniques et stratégiques en ingénierie des données grâce à une combinaison de résolution de problèmes, conception de systèmes et flexibilité de pensée.
