import time
from utils import get_db_connection
from models import DimTemps, DimLieux, DimConditionsMeteo
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
    INSERT INTO DimTemps (date, annee, mois, jour, heure, minute, jour_semaine, nom_mois)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE date = VALUES(date)
    """
    print("INFO: Executing query to fetch distinct datetime_observation values from intermediate database...")
    cursor_source.execute(query_source)
    rows = cursor_source.fetchall()
    print(rows)
    print(f"INFO: Found {len(rows)} distinct datetime_observation values in intermediate database.")

    for row in rows:
        time.sleep(0.5)  # Pause to avoid CPU throttling
        datetime_observation = row["datetime_observation"]
        print(f"INFO: Processing datetime_observation '{datetime_observation}'")

        # Ensure datetime_observation is a datetime object
        try:
            if isinstance(datetime_observation, str):
                dt = datetime.strptime(datetime_observation, "%Y-%m-%d %H:%M:%S")
            elif isinstance(datetime_observation, datetime):
                dt = datetime_observation
            else:
                print(f"WARNING: Unexpected type for datetime_observation: {type(datetime_observation)}")
                continue
        except ValueError as e:
            print(f"ERROR: Failed to parse datetime_observation '{datetime_observation}' - {e}")
            continue

        print(f"INFO: Parsed datetime_observation '{datetime_observation}' into datetime object '{dt}'")

        dim_temps = DimTemps(
            date=dt.strftime("%Y-%m-%d"),
            annee=dt.year,
            mois=dt.month,
            jour=dt.day,
            heure=dt.hour,  # Extract hour from datetime_observation
            minute=dt.minute,  # Extract minute from datetime_observation
            jour_semaine=dt.strftime("%A"),
            nom_mois=dt.strftime("%B"),
        )
        print(f"INFO: Prepared DimTemps object: {dim_temps}")

        try:
            cursor_target.execute(
                query_target,
                (
                    str(dim_temps.date),
                    dim_temps.annee,
                    dim_temps.mois,
                    dim_temps.jour,
                    dim_temps.heure,
                    dim_temps.minute,
                    dim_temps.jour_semaine,
                    dim_temps.nom_mois,
                ),
            )
            print(f"INFO: Successfully inserted date '{dim_temps.date}' into DimTemps.")
        except Exception as e:
            print(f"ERROR: Failed to insert date '{dim_temps.date}' into DimTemps - {e}")
            continue
        time.sleep(0.5)  # Pause after each insertion


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
        time.sleep(0.5)  # Pause to avoid CPU throttling
        dim_lieux = DimLieux(
            nom_ville=row["nom"],
            region=row["region"],
            pays=row["pays"],
        )
        cursor_target.execute(
            query_target,
            (dim_lieux.nom_ville, dim_lieux.region, dim_lieux.pays),
        )
        print(f"INFO: Inserted or updated location '{dim_lieux.nom_ville}' in DimLieux.")
        time.sleep(0.5)  # Pause after each insertion


def transfer_dim_conditions_meteo(cursor_source, cursor_target) -> None:
    """
    Transfers data from the intermediate database to the DimConditionsMeteo table in the warehouse.
    """
    query_source = """
    SELECT DISTINCT code_condition, texte_condition
    FROM conditions_meteo
    """
    query_target = """
    INSERT INTO DimConditionsMeteo (code_condition, texte_condition)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE texte_condition = VALUES(texte_condition)
    """
    cursor_source.execute(query_source)
    for row in cursor_source.fetchall():
        time.sleep(0.5)  # Pause to avoid CPU throttling
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
        print(f"INFO: Inserted or updated condition '{dim_conditions.code_condition}' in DimConditionsMeteo.")
        time.sleep(0.5)  # Pause after each insertion


def transfer_fait_donnees_meteo(cursor_source, cursor_target) -> None:
    """
    Transfers data from the intermediate database to the FaitDonneesMeteo table in the warehouse.
    """
    query_source = """
    SELECT dm.id_lieu, dm.datetime_observation AS date_observation, dm.code_condition,
           dm.temperature_celsius, dm.vent_kph, dm.vent_degre, dm.direction_vent,
           dm.pression_millibars, dm.precipitation_mm, dm.humidite_pourcentage,
           dm.nuages_pourcentage, dm.visibilite_km, dm.indice_uv, dm.rafales_kph
    FROM donnees_meteo dm
    """
    query_lieux = """
    SELECT nom FROM lieux WHERE id_lieu = %s
    """
    query_dimtemps_insert = """
    INSERT INTO DimTemps (date, annee, mois, jour, heure, minute, jour_semaine, nom_mois)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE date = VALUES(date)
    """
    query_target = """
    INSERT INTO FaitDonneesMeteo (
        id_dim_lieu_fk, id_dim_temps_fk, id_dim_condition_fk,
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
        time.sleep(0.5)  # Pause to avoid CPU throttling
        print(f"INFO: Processing row with id_lieu '{row['id_lieu']}' and date_observation '{row['date_observation']}'")

        # Get the location name from the intermediate DB's lieux table
        cursor_source.execute(query_lieux, (row["id_lieu"],))
        lieux_result = cursor_source.fetchone()
        if lieux_result is None:
            print(f"WARNING: No matching location found for id_lieu '{row['id_lieu']}' in lieux table.")
            continue
        nom_ville = lieux_result["nom"]
        print(f"INFO: Found location name '{nom_ville}' for id_lieu '{row['id_lieu']}'")

        # Map nom_ville to id_dim_lieu in the warehouse DB
        cursor_target.execute("SELECT id_dim_lieu FROM DimLieux WHERE nom_ville = %s", (nom_ville,))
        dim_lieux_result = cursor_target.fetchone()
        if dim_lieux_result is None:
            print(f"WARNING: No matching id_dim_lieu found for nom_ville '{nom_ville}' in DimLieux.")
            continue
        id_dim_lieu_fk = dim_lieux_result["id_dim_lieu"]
        print(f"INFO: Found id_dim_lieu '{id_dim_lieu_fk}' for nom_ville '{nom_ville}'")

        # Convert date_observation to a string
        try:
            date_str = row["date_observation"].strftime("%Y-%m-%d") 
            print(f"INFO: Formatted date_observation '{row['date_observation']}' as '{date_str}'")
        except AttributeError as e:
            print(f"ERROR: Failed to format date_observation '{row['date_observation']}' - {e}")
            continue

        # Check if date_str exists in DimTemps, and insert if not, then get id_dim_temps
        print(f"INFO: Checking if date '{date_str}' exists in DimTemps...")
        cursor_target.execute("SELECT id_dim_temps FROM DimTemps WHERE date = %s", (date_str,))
        dim_temps_result = cursor_target.fetchone()

        if dim_temps_result is None:
            print(f"WARNING: No matching id_dim_temps found for date '{date_str}' in DimTemps. Creating it...")
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
            cursor_target.execute(
                query_dimtemps_insert,
                (
                    date_str,
                    dt.year,
                    dt.month,
                    dt.day,
                    0,  # Default to 0 since time is removed
                    0,  # Default to 0 since time is removed
                    dt.strftime("%A"),
                    dt.strftime("%B"),
                ),
            )
            print(f"INFO: Successfully created date '{date_str}' in DimTemps. Now fetching its id_dim_temps...")
            cursor_target.execute("SELECT id_dim_temps FROM DimTemps WHERE date = %s", (date_str,))
            dim_temps_result = cursor_target.fetchone()
            if dim_temps_result is None: # Should not happen if insert was successful
                print(f"ERROR: Could not retrieve id_dim_temps for newly inserted date '{date_str}'. Skipping row.")
                continue
        id_dim_temps_fk = dim_temps_result["id_dim_temps"]
        print(f"INFO: Found id_dim_temps '{id_dim_temps_fk}' for date '{date_str}'")


        # Get id_dim_condition_fk from DimConditionsMeteo
        cursor_target.execute("SELECT id_dim_condition FROM DimConditionsMeteo WHERE code_condition = %s", (row["code_condition"],))
        dim_condition_result = cursor_target.fetchone()
        if dim_condition_result is None:
            print(f"WARNING: No matching id_dim_condition found for code_condition '{row['code_condition']}' in DimConditionsMeteo.")
            continue
        id_dim_condition_fk = dim_condition_result["id_dim_condition"]
        print(f"INFO: Found id_dim_condition '{id_dim_condition_fk}' for code_condition '{row['code_condition']}'")


        # Insert data into FaitDonneesMeteo
        cursor_target.execute(
            query_target,
            (
                id_dim_lieu_fk,
                id_dim_temps_fk,  # Use the mapped id_dim_temps_fk
                id_dim_condition_fk, # Use the mapped id_dim_condition_fk
                row["temperature_celsius"],
                row["vent_kph"],
                row["vent_degre"],
                row["direction_vent"],
                row["pression_millibars"],
                row["precipitation_mm"],
                row["humidite_pourcentage"],
                row["nuages_pourcentage"],
                row["visibilite_km"],
                row["indice_uv"],
                row["rafales_kph"],
            ),
        )
        print(f"INFO: Successfully inserted data for id_lieu '{row['id_lieu']}' and date_observation '{date_str}'")
        time.sleep(0.5)  # Pause after each insertion


def transfer_data_to_warehouse() -> None:
    """
    Main function to transfer data from the intermediate database to the warehouse.
    """
    print("INFO: Establishing database connections...")
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
        time.sleep(0.5)
        print("INFO: DimTemps transfer completed successfully.")

        print("INFO: Transferring DimLieux...")
        transfer_dim_lieux(cursor_source, cursor_target)
        time.sleep(0.5)
        print("INFO: DimLieux transfer completed successfully.")

        print("INFO: Transferring DimConditionsMeteo...")
        transfer_dim_conditions_meteo(cursor_source, cursor_target)
        time.sleep(0.5)
        print("INFO: DimConditionsMeteo transfer completed successfully.")

        print("INFO: Transferring FaitDonneesMeteo...")
        transfer_fait_donnees_meteo(cursor_source, cursor_target)
        time.sleep(0.5)
        print("INFO: FaitDonneesMeteo transfer completed successfully.")

        conn_target.commit()
        print("SUCCESS: Data transfer to warehouse completed.")
    except Exception as e:
        print(f"ERROR: Data transfer failed - {e}")
        conn_target.rollback()
    finally:
        print("INFO: Closing database connections...")
        cursor_source.close()
        cursor_target.close()
        conn_source.close()
        conn_target.close()
        print("INFO: Database connections closed.")


if __name__ == "__main__":
    transfer_data_to_warehouse()