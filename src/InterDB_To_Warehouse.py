from utils import get_db_connection
from models import DimTemps, DimLieux, DimConditionsMeteo, FaitDonneesMeteo
from datetime import datetime


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
        dt = datetime.strptime(datetime_key, "%Y-%m-%d %H:%M:%S")
        dim_temps = DimTemps(
            datetime_key=datetime_key,
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
                dim_temps.datetime_key,
                dim_temps.annee,
                dim_temps.mois,
                dim_temps.jour,
                dim_temps.heure,
                dim_temps.minute,
                dim_temps.jour_semaine,
                dim_temps.nom_mois,
            ),
        )


def transfer_dim_lieux(cursor_source, cursor_target) -> None:
    """
    Transfers data from the intermediate database to the DimLieux table in the warehouse.
    """
    query_source = """
    SELECT DISTINCT nom, region, pays
    FROM lieux
    """
    query_target = """
    INSERT INTO DimLieux (nom_ville, region, pays)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE nom_ville = VALUES(nom_ville)
    """
    cursor_source.execute(query_source)
    for row in cursor_source.fetchall():
        dim_lieux = DimLieux(
            nom_ville=row["nom"],
            region=row["region"],
            pays=row["pays"],
        )
        cursor_target.execute(
            query_target,
            (dim_lieux.nom_ville, dim_lieux.region, dim_lieux.pays),
        )


def transfer_dim_conditions_meteo(cursor_source, cursor_target) -> None:
    """
    Transfers data from the intermediate database to the DimConditionsMeteo table in the warehouse.
    """
    query_source = """
    SELECT DISTINCT code_condition, texte_condition
    FROM conditions_meteo
    """
    query_target = """
    INSERT INTO DimConditionsMeteo (id_dim_condition, code_condition, texte_condition)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE texte_condition = VALUES(texte_condition)
    """
    cursor_source.execute(query_source)
    for row in cursor_source.fetchall():
        dim_conditions = DimConditionsMeteo(
            code_condition=row["code_condition"],
            texte_condition=row["texte_condition"],
        )
        cursor_target.execute(
            query_target,
            (
                dim_conditions.code_condition,
                dim_conditions.texte_condition,
            ),
        )


def transfer_fait_donnees_meteo(cursor_source, cursor_target) -> None:
    """
    Transfers data from the intermediate database to the FaitDonneesMeteo table in the warehouse.
    """
    query_source = """
    SELECT dm.id_lieu, dm.datetime_observation, dm.code_condition,
           dm.temperature_celsius, dm.vent_kph, dm.vent_degre, dm.direction_vent,
           dm.pression_millibars, dm.precipitation_mm, dm.humidite_pourcentage,
           dm.nuages_pourcentage, dm.visibilite_km, dm.indice_uv, dm.rafales_kph
    FROM donnees_meteo dm
    """
    query_target = """
    INSERT INTO FaitDonneesMeteo (
        id_dim_lieu_fk, datetime_fk, id_dim_condition_fk,
        temperature_celsius, vent_kph, vent_degre, direction_vent,
        pression_millibars, precipitation_mm, humidite_pourcentage,
        nuages_pourcentage, visibilite_km, indice_uv, rafales_kph
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        temperature_celsius = VALUES(temperature_celsius),
        vent_kph = VALUES(vent_kph),
        vent_degre = VALUES(vent_degre),
        direction_vent = VALUES(direction_vent),
        pression_millibars = VALUES(pression_millibars),
        precipitation_mm = VALUES(precipitation_mm),
        humidite_pourcentage = VALUES(humidite_pourcentage),
        nuages_pourcentage = VALUES(nuages_pourcentage),
        visibilite_km = VALUES(visibilite_km),
        indice_uv = VALUES(indice_uv),
        rafales_kph = VALUES(rafales_kph)
    """
    cursor_source.execute(query_source)
    for row in cursor_source.fetchall():
        fait_donnees = FaitDonneesMeteo(
            id_dim_lieu_fk=row["id_lieu"],
            datetime_fk=row["datetime_observation"],
            id_dim_condition_fk=row["code_condition"],
            temperature_celsius=row["temperature_celsius"],
            vent_kph=row["vent_kph"],
            vent_degre=row["vent_degre"],
            direction_vent=row["direction_vent"],
            pression_millibars=row["pression_millibars"],
            precipitation_mm=row["precipitation_mm"],
            humidite_pourcentage=row["humidite_pourcentage"],
            nuages_pourcentage=row["nuages_pourcentage"],
            visibilite_km=row["visibilite_km"],
            indice_uv=row["indice_uv"],
            rafales_kph=row["rafales_kph"],
        )
        cursor_target.execute(
            query_target,
            (
                fait_donnees.id_dim_lieu_fk,
                fait_donnees.datetime_fk,
                fait_donnees.id_dim_condition_fk,
                fait_donnees.temperature_celsius,
                fait_donnees.vent_kph,
                fait_donnees.vent_degre,
                fait_donnees.direction_vent,
                fait_donnees.pression_millibars,
                fait_donnees.precipitation_mm,
                fait_donnees.humidite_pourcentage,
                fait_donnees.nuages_pourcentage,
                fait_donnees.visibilite_km,
                fait_donnees.indice_uv,
                fait_donnees.rafales_kph,
            ),
        )


def transfer_data_to_warehouse() -> None:
    """
    Main function to transfer data from the intermediate database to the warehouse.
    """
    conn_source = get_db_connection(db_name="meteo")  # Intermediate DB
    conn_target = get_db_connection(db_name="meteo_warehouse")  # Warehouse DB

    if not conn_source or not conn_target:
        print("ERROR: Failed to establish database connections.")
        return

    cursor_source = conn_source.cursor()
    cursor_target = conn_target.cursor()

    try:
        print("INFO: Transferring DimTemps...")
        transfer_dim_temps(cursor_source, cursor_target)

        print("INFO: Transferring DimLieux...")
        transfer_dim_lieux(cursor_source, cursor_target)

        print("INFO: Transferring DimConditionsMeteo...")
        transfer_dim_conditions_meteo(cursor_source, cursor_target)

        print("INFO: Transferring FaitDonneesMeteo...")
        transfer_fait_donnees_meteo(cursor_source, cursor_target)

        conn_target.commit()
        print("SUCCESS: Data transfer to warehouse completed.")
    except Exception as e:
        print(f"ERROR: Data transfer failed - {e}")
        conn_target.rollback()
    finally:
        cursor_source.close()
        cursor_target.close()
        conn_source.close()
        conn_target.close()


if __name__ == "__main__":
    transfer_data_to_warehouse()