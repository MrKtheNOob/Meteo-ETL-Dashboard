import pymysql
import pandas as pd
from datetime import date
from typing import Optional, List, Dict, Any, Tuple
import os

from pymysql import cursors
from pymysql.connections import Connection

from utils import get_db_connection

pymysql.install_as_MySQLdb()


def extract_data_to_dataframe(conn: Connection, query: str) -> pd.DataFrame:
    """Extracts data from a database using a query and returns a pandas DataFrame."""
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query)
            data: List[Dict[str, Any]] = cursor.fetchall()
        df = pd.DataFrame(data)
        print(f"INFO: Extracted {len(df)} rows from query.")
        return df
    except Exception as e:
        print(f"ERROR: Error extracting data from query: {e}")
        return pd.DataFrame()


def load_data_bulk_upsert(
    cursor: pymysql.cursors.Cursor,
    table_name: str,
    columns: List[str],
    data: List[Tuple[Any, ...]],
    unique_key_columns: List[
        str
    ],  # Columns that form the unique key for ON DUPLICATE KEY UPDATE
) -> int:
    """
    Performs a bulk upsert (INSERT...ON DUPLICATE KEY UPDATE) using pymysql's executemany.
    Returns the number of rows affected.
    """
    if not data:
        print(
            f"INFO: No data to insert/update into {table_name}. Skipping bulk operation."
        )
        return 0

    placeholders = ", ".join(["%s"] * len(columns))
    cols_str = ", ".join(columns)

    update_parts = [
        f"{col} = VALUES({col})" for col in columns if col not in unique_key_columns
    ]

    if not update_parts:
        update_str = f"{unique_key_columns[0]} = VALUES({unique_key_columns[0]})"
    else:
        update_str = ", ".join(update_parts)

    query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_str}"

    try:
        print(f"INFO: Attempting to bulk upsert {len(data)} rows into {table_name}...")
        cursor.executemany(query, data)
        print(
            f"SUCCESS: Bulk upsert into {table_name} completed. Rows affected: {cursor.rowcount}."
        )
        return cursor.rowcount
    except Exception as e:
        print(f"ERROR: Failed to bulk upsert into {table_name}: {e}")
        raise


def transform_load_to_warehouse() -> None:
    """Main ETL process to extract, transform, and incrementally load data into the star schema."""
    source_conn: Optional[Connection] = None
    target_conn: Optional[Connection] = None

    try:
        # --- 1. Establish Connections ---
        print("INFO: Attempting to establish database connections...")
        source_conn = get_db_connection("meteo")
        target_conn = get_db_connection("meteo_warehouse")

        if not source_conn or not target_conn:
            print(
                "ERROR: Failed to establish one or both database connections. Exiting."
            )
            return
        print("SUCCESS: PyMySQL connections established.")

        target_cursor = target_conn.cursor()

        # --- 2. Extract Data from Source ---
        print("\nINFO: Beginning data extraction from source database.")
        df_lieux_source: pd.DataFrame = extract_data_to_dataframe(
            source_conn, "SELECT id_lieu, nom, region, pays FROM lieux"
        )
        df_conditions_source: pd.DataFrame = extract_data_to_dataframe(
            source_conn, "SELECT code_condition, texte_condition FROM conditions_meteo"
        )
        df_donnees_source: pd.DataFrame = extract_data_to_dataframe(
            source_conn, "SELECT * FROM donnees_meteo"
        )

        if (
            df_lieux_source.empty
            or df_conditions_source.empty
            or df_donnees_source.empty
        ):
            print(
                "ERROR: One or more source tables are empty or failed to extract. Exiting."
            )
            return
        print("SUCCESS: All necessary data extracted from source tables.")

        # --- 3. Transform Data and Prepare for Dimension Upserts ---
        print("\nINFO: Beginning data transformation for dimension tables.")

        ## Corrected section for DimConditionsMeteo
        print("INFO: Preparing data for DimConditionsMeteo...")
        # DimConditionsMeteo should be populated directly from df_conditions_source
        # as it represents the master list of conditions.
        # df_conditions_source already contains 'code_condition' and 'texte_condition'.
        dim_conditions_data = [
            (row["code_condition"], row["texte_condition"])
            for _, row in df_conditions_source.iterrows()
        ]
        print(
            f"SUCCESS: Prepared {len(dim_conditions_data)} unique conditions for DimConditionsMeteo."
        )
        ## End of corrected section

        # 3.2. Transform DimLieux
        print("INFO: Preparing data for DimLieux...")
        dim_lieux_df: pd.DataFrame = df_lieux_source[
            ["nom", "region", "pays"]
        ].drop_duplicates()
        dim_lieux_data = [
            (row["nom"], row["region"], row["pays"])
            for _, row in dim_lieux_df.iterrows()
        ]
        print(f"SUCCESS: Prepared {len(dim_lieux_data)} unique locations for DimLieux.")

        # 3.3. Transform DimTemps
        print("INFO: Preparing data for DimTemps...")
        initial_na_count = df_donnees_source["datetime_observation"].isna().sum()
        df_donnees_source["datetime_observation"] = pd.to_datetime(
            df_donnees_source["datetime_observation"],
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce",
        )
        final_na_count = df_donnees_source["datetime_observation"].isna().sum()
        if final_na_count > initial_na_count:
            print(
                f"WARNING: {final_na_count - initial_na_count} 'datetime_observation' values could not be parsed and were coerced to NaT. These records will be skipped in fact table loading."
            )

        df_donnees_valid_time = df_donnees_source.dropna(
            subset=["datetime_observation"]
        )

        dim_temps_df: pd.DataFrame = pd.DataFrame(
            {
                "date": df_donnees_valid_time["datetime_observation"].dt.date,
                "annee": df_donnees_valid_time["datetime_observation"].dt.year,
                "mois": df_donnees_valid_time["datetime_observation"].dt.month,
                "jour": df_donnees_valid_time["datetime_observation"].dt.day,
                "heure": df_donnees_valid_time["datetime_observation"].dt.hour,
                "minute": df_donnees_valid_time["datetime_observation"].dt.minute,
                "jour_semaine": df_donnees_valid_time[
                    "datetime_observation"
                ].dt.day_name(),
                "nom_mois": df_donnees_valid_time[
                    "datetime_observation"
                ].dt.month_name(),
            }
        ).drop_duplicates()

        dim_temps_data = [
            (
                row["date"],
                row["annee"],
                row["mois"],
                row["jour"],
                row["heure"],
                row["minute"],
                row["jour_semaine"],
                row["nom_mois"],
            )
            for _, row in dim_temps_df.iterrows()
        ]
        print(
            f"SUCCESS: Prepared {len(dim_temps_data)} unique time entries for DimTemps."
        )

        # --- 4. Load Dimension Tables (Upsert) and Retrieve All Surrogate Keys ---
        print(
            "\nINFO: Loading dimension data into target database (upserting) and retrieving surrogate keys."
        )
        target_conn.begin()

        load_data_bulk_upsert(
            target_cursor,
            "DimConditionsMeteo",
            ["code_condition", "texte_condition"],
            dim_conditions_data,
            ["code_condition"],
        )

        load_data_bulk_upsert(
            target_cursor,
            "DimLieux",
            ["nom_ville", "region", "pays"],
            dim_lieux_data,
            ["nom_ville"],
        )

        load_data_bulk_upsert(
            target_cursor,
            "DimTemps",
            [
                "date",
                "annee",
                "mois",
                "jour",
                "heure",
                "minute",
                "jour_semaine",
                "nom_mois",
            ],
            dim_temps_data,
            ["date", "annee", "mois", "jour", "heure", "minute"],
        )

        print(
            "INFO: Reading back all surrogate keys from target dimension tables for mapping."
        )
        df_dim_lieux_target_full: pd.DataFrame = extract_data_to_dataframe(
            target_conn, "SELECT id_dim_lieu, nom_ville, region, pays FROM DimLieux"
        )
        df_dim_conditions_target_full: pd.DataFrame = extract_data_to_dataframe(
            target_conn,
            "SELECT id_dim_condition, code_condition FROM DimConditionsMeteo",
        )
        df_dim_temps_target_full: pd.DataFrame = extract_data_to_dataframe(
            target_conn,
            "SELECT id_dim_temps, date, annee, mois, jour, heure, minute FROM DimTemps",
        )
        print("SUCCESS: All surrogate keys retrieved.")

        lieu_nk_to_sk: Dict[Tuple[str, str, str], int] = {
            (row["nom_ville"], row["region"], row["pays"]): row["id_dim_lieu"]
            for _, row in df_dim_lieux_target_full.iterrows()
        }
        condition_nk_to_sk: Dict[int, int] = {
            row["code_condition"]: row["id_dim_condition"]
            for _, row in df_dim_conditions_target_full.iterrows()
        }
        df_dim_temps_target_full["date"] = pd.to_datetime(
            df_dim_temps_target_full["date"]
        ).dt.date
        temps_nk_to_sk: Dict[Tuple[date, int, int, int, int, int], int] = {
            (
                row["date"],
                row["annee"],
                row["mois"],
                row["jour"],
                row["heure"],
                row["minute"],
            ): row["id_dim_temps"]
            for _, row in df_dim_temps_target_full.iterrows()
        }
        print("SUCCESS: Natural key to surrogate key mappings created.")

        # --- 5. Prepare and Load Fact Table ---
        print("\nINFO: Preparing data for FaitDonneesMeteo (Fact Table).")
        fait_donnees_meteo_data: List[Tuple[Any, ...]] = []

        # Merge source location details to df_donnees_valid_time to get natural keys for joining
        df_donnees_fact_prep = pd.merge(
            df_donnees_valid_time,
            df_lieux_source[["id_lieu", "nom", "region", "pays"]],
            on="id_lieu",
            how="left",
        )

        # Add surrogate keys to the DataFrame first for easier processing
        df_donnees_fact_prep["id_dim_lieu_fk"] = df_donnees_fact_prep.apply(
            lambda row: lieu_nk_to_sk.get((row["nom"], row["region"], row["pays"])),
            axis=1,
        )

        # Ensure that code_condition exists in df_donnees_fact_prep before mapping
        # If code_condition might be missing, handle with .get() or dropna prior
        df_donnees_fact_prep["id_dim_condition_fk"] = df_donnees_fact_prep[
            "code_condition"
        ].map(condition_nk_to_sk)

        df_donnees_fact_prep["id_dim_temps_fk"] = df_donnees_fact_prep[
            "datetime_observation"
        ].apply(
            lambda dt: (
                temps_nk_to_sk.get(
                    (dt.date(), dt.year, dt.month, dt.day, dt.hour, dt.minute)
                )
                if pd.notna(dt)
                else None
            )
        )

        fks_to_check = ["id_dim_lieu_fk", "id_dim_temps_fk", "id_dim_condition_fk"]
        initial_fact_rows = len(df_donnees_fact_prep)
        df_fact_final = df_donnees_fact_prep.dropna(subset=fks_to_check)
        if len(df_fact_final) < initial_fact_rows:
            print(
                f"WARNING: Dropped {initial_fact_rows - len(df_fact_final)} rows from fact table due to NULL foreign keys."
            )
            print(
                "         This indicates a mismatch between source data and dimension tables."
            )

        for _, row in df_fact_final.iterrows():
            fait_donnees_meteo_data.append(
                (
                    int(row["id_dim_lieu_fk"]),
                    int(row["id_dim_temps_fk"]),
                    int(row["id_dim_condition_fk"]),
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
                )
            )

        print(
            f"SUCCESS: Prepared {len(fait_donnees_meteo_data)} rows for FaitDonneesMeteo (after FK resolution)."
        )

        fact_unique_key = ["id_dim_lieu_fk", "id_dim_temps_fk"]

        load_data_bulk_upsert(
            target_cursor,
            "FaitDonneesMeteo",
            [
                "id_dim_lieu_fk",
                "id_dim_temps_fk",
                "id_dim_condition_fk",
                "temperature_celsius",
                "vent_kph",
                "vent_degre",
                "direction_vent",
                "pression_millibars",
                "precipitation_mm",
                "humidite_pourcentage",
                "nuages_pourcentage",
                "visibilite_km",
                "indice_uv",
                "rafales_kph",
            ],
            fait_donnees_meteo_data,
            fact_unique_key,
        )

        target_conn.commit()
        print("SUCCESS: Fact table loaded and committed.")

        print("\nSUCCESS: ETL process completed successfully!")

    except Exception as e:
        print(f"CRITICAL ERROR: An error occurred during the ETL process: {e}")
        if target_conn:
            target_conn.rollback()
            print("INFO: Database transaction rolled back due to error.")
    finally:
        print("INFO: Attempting to close database connections.")
        if source_conn:
            source_conn.close()
            print("INFO: Source database connection closed.")
        if target_conn:
            target_conn.close()
            print("INFO: Target database connection closed.")
        print("SUCCESS: All database connections handled.")


if __name__ == "__main__":
    transform_load_to_warehouse()
    print("INFO: ETL process script completed. Check logs for details.")
