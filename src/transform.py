import os
import pymysql
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, date
from typing import Optional, cast, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from utils import get_db_connection 

load_dotenv()

pymysql.install_as_MySQLdb()

DB_SQL_ALCHEMY_URLS = {
    'source_db_url': f"{os.getenv("DB_LINK")}/meteo",
    'target_db_url': f"{os.getenv("DB_LINK")}/meteo_warehouse"
}

def extract_data_to_dataframe(conn: pymysql.connections.Connection, query: str) -> pd.DataFrame:
    """Extracts data from a database using a query and returns a pandas DataFrame."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            data: List[Dict[str, Any]] = cursor.fetchall()
            # If using DictCursor, keys are column names. If not, get from cursor.description
            columns: List[str] = [desc[0] for desc in cursor.description] if cursor.description else []

        df = pd.DataFrame(data, columns=columns)
        print(f"INFO: Extracted {len(df)} rows from query.")
        return df
    except Exception as e:
        print(f"ERROR: Error extracting data from query: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

def load_dataframe_to_db(df: pd.DataFrame, engine: Engine, table_name: str, if_exists_option: str = 'append', index: bool = False) -> None:
    """Loads a pandas DataFrame into a specified database table using a SQLAlchemy engine."""
    try:
        # Use pandas to_sql method with the SQLAlchemy engine
        df.to_sql(name=table_name, con=engine, if_exists=if_exists_option, index=index)
        print(f"SUCCESS: Loaded {len(df)} rows into {table_name}.")
    except Exception as e:
        print(f"ERROR: Error loading data into {table_name}: {e}")

def transform_load_to_warehouse() -> None:
    """Main ETL process to extract, transform, and load data."""
    source_conn: Optional[pymysql.connections.Connection] = None
    target_conn: Optional[pymysql.connections.Connection] = None
    target_engine: Optional[Engine] = None
    try:
        print("INFO: Starting ETL process...")
        # --- 1. Establish Connections ---
        print("INFO: Attempting to establish database connections...")
        # Get pymysql connections for extraction
        source_conn = get_db_connection("meteo")          # Your schema2 database name
        target_conn = get_db_connection("meteo_warehouse")      # Your star_schema database name

        if not source_conn or not target_conn:
            print("ERROR: Failed to establish one or both database connections. Exiting.")
            return
        print("SUCCESS: PyMySQL connections established.")

        # Create SQLAlchemy engine for loading into target database
        try:
            target_engine = create_engine(DB_SQL_ALCHEMY_URLS['target_db_url'])
            # Test connection
            with target_engine.connect() as connection:
                connection.close()
            print("SUCCESS: SQLAlchemy engine for target database created and tested.")
        except Exception as e:
            print(f"ERROR: Could not create SQLAlchemy Engine for target database: {e}")
            return


        # --- 2. Extract Data from Source ---
        print("\nINFO: Beginning data extraction from source database.")
        df_lieux_source: pd.DataFrame = cast(pd.DataFrame, extract_data_to_dataframe(source_conn, "SELECT id_lieu, nom, region, pays FROM lieux"))
        df_conditions_source: pd.DataFrame = cast(pd.DataFrame, extract_data_to_dataframe(source_conn, "SELECT code_condition, texte_condition FROM conditions_meteo"))
        df_donnees_source: pd.DataFrame = cast(pd.DataFrame, extract_data_to_dataframe(source_conn, "SELECT * FROM donnees_meteo"))

        if df_lieux_source.empty or df_conditions_source.empty or df_donnees_source.empty:
            print("ERROR: One or more source tables are empty or failed to extract. Exiting.")
            return
        print("SUCCESS: All necessary data extracted from source tables.")

        # --- 3. Transform Data ---
        print("\nINFO: Beginning data transformation for dimension tables.")

        # 3.1. Transform DimLieux
        print("INFO: Transforming data for DimLieux...")
        df_dim_lieux: pd.DataFrame = df_lieux_source[['nom', 'region', 'pays']].drop_duplicates()
        df_dim_lieux = df_dim_lieux.rename(columns={'nom': 'nom_ville'})
        print(f"SUCCESS: Transformed {len(df_dim_lieux)} unique locations for DimLieux.")

        # 3.2. Transform DimConditionsMeteo
        print("INFO: Transforming data for DimConditionsMeteo...")
        df_dim_conditions: pd.DataFrame = df_conditions_source[['code_condition', 'texte_condition']].drop_duplicates()
        print(f"SUCCESS: Transformed {len(df_dim_conditions)} unique conditions for DimConditionsMeteo.")

        # 3.3. Transform DimTemps
        print("INFO: Transforming data for DimTemps...")
        initial_na_count = df_donnees_source['datetime_observation'].isna().sum()
        df_donnees_source['datetime_observation'] = pd.to_datetime(
            df_donnees_source['datetime_observation'],
            format='%Y-%m-%d %H:%M:%S',
            errors='coerce'
        )
        final_na_count = df_donnees_source['datetime_observation'].isna().sum()
        if final_na_count > initial_na_count:
            print(f"WARNING: {final_na_count - initial_na_count} 'datetime_observation' values could not be parsed and were coerced to NaT.")

        df_dim_temps: pd.DataFrame = pd.DataFrame({
            'date': df_donnees_source['datetime_observation'].dt.date,
            'annee': df_donnees_source['datetime_observation'].dt.year,
            'mois': df_donnees_source['datetime_observation'].dt.month,
            'jour': df_donnees_source['datetime_observation'].dt.day,
            'heure': df_donnees_source['datetime_observation'].dt.hour,
            'minute': df_donnees_source['datetime_observation'].dt.minute,
            'jour_semaine': df_donnees_source['datetime_observation'].dt.day_name(),
            'nom_mois': df_donnees_source['datetime_observation'].dt.month_name()
        }).drop_duplicates()
        print(f"SUCCESS: Transformed {len(df_dim_temps)} unique time entries for DimTemps.")

        # 3.4. Transform FaitDonneesMeteo (Fact Table)
        print("\nINFO: Preparing data for FaitDonneesMeteo (Fact Table).")
        # Ensure these operations are done AFTER datetime conversion
        df_donnees_source['temp_date'] = df_donnees_source['datetime_observation'].dt.date
        df_donnees_source['temp_annee'] = df_donnees_source['datetime_observation'].dt.year
        df_donnees_source['temp_mois'] = df_donnees_source['datetime_observation'].dt.month
        df_donnees_source['temp_jour'] = df_donnees_source['datetime_observation'].dt.day
        df_donnees_source['temp_heure'] = df_donnees_source['datetime_observation'].dt.hour
        df_donnees_source['temp_minute'] = df_donnees_source['datetime_observation'].dt.minute


        # --- 4. Load Dimension Tables to Target DB (then read back IDs for fact table) ---
        print("\nINFO: Loading dimension data into target database.")
        load_dataframe_to_db(df_dim_lieux, target_engine, 'DimLieux', if_exists_option='append')
        load_dataframe_to_db(df_dim_conditions, target_engine, 'DimConditionsMeteo', if_exists_option='append')
        load_dataframe_to_db(df_dim_temps, target_engine, 'DimTemps', if_exists_option='append')
        print("SUCCESS: Dimension tables loaded.")

        print("INFO: Reading back surrogate keys from target dimension tables.")
        # Use target_conn (pymysql connection) for reading back surrogate keys from the target DB
        df_dim_lieux_target: pd.DataFrame = cast(pd.DataFrame, extract_data_to_dataframe(target_conn, "SELECT id_dim_lieu, nom_ville, region, pays FROM DimLieux"))
        df_dim_conditions_target: pd.DataFrame = cast(pd.DataFrame, extract_data_to_dataframe(target_conn, "SELECT id_dim_condition, code_condition, texte_condition FROM DimConditionsMeteo"))
        df_dim_temps_target: pd.DataFrame = cast(pd.DataFrame, extract_data_to_dataframe(target_conn, "SELECT id_dim_temps, date, annee, mois, jour, heure, minute FROM DimTemps"))
        print("SUCCESS: Surrogate keys retrieved.")

        # Convert 'date' column in target DimTemps to datetime.date objects for robust merging
        df_dim_temps_target['date'] = pd.to_datetime(df_dim_temps_target['date']).dt.date

        # Join source fact data with loaded dimension data to get surrogate keys
        print("INFO: Joining fact data with dimension surrogate keys.")
        df_fait: pd.DataFrame = df_donnees_source.copy()

        # Merge with DimLieux to get id_dim_lieu_fk
        print("INFO: Merging with DimLieux to get id_dim_lieu_fk...")
        df_fait = pd.merge(df_fait, df_lieux_source[['id_lieu', 'nom', 'region', 'pays']], on='id_lieu', how='left')
        df_fait = pd.merge(df_fait, df_dim_lieux_target,
                           left_on=['nom', 'region', 'pays'],
                           right_on=['nom_ville', 'region', 'pays'],
                           how='left')
        # Check for NaN in the merged foreign key column
        missing_lieu_fks = df_fait['id_dim_lieu'].isna().sum()
        if missing_lieu_fks > 0:
            print(f"WARNING: {missing_lieu_fks} records in FaitDonneesMeteo could not find a matching DimLieux entry. Check data consistency.")
            # Option: Drop rows with missing FKs if they are strictly required.
            # df_fait.dropna(subset=['id_dim_lieu'], inplace=True)
        df_fait = df_fait.drop(columns=['nom', 'region', 'pays', 'nom_ville'])
        print(f"INFO: After DimLieux merge. Records with id_dim_lieu: {df_fait['id_dim_lieu'].notna().sum()}/{len(df_fait)}.")


        # Merge with DimConditionsMeteo to get id_dim_condition_fk
        print("INFO: Merging with DimConditionsMeteo to get id_dim_condition_fk...")
        df_fait = pd.merge(df_fait, df_conditions_source[['code_condition', 'texte_condition']], on='code_condition', how='left')
        df_fait = pd.merge(df_fait, df_dim_conditions_target,
                           left_on=['code_condition', 'texte_condition'],
                           right_on=['code_condition', 'texte_condition'],
                           how='left')
        missing_condition_fks = df_fait['id_dim_condition'].isna().sum()
        if missing_condition_fks > 0:
            print(f"WARNING: {missing_condition_fks} records in FaitDonneesMeteo could not find a matching DimConditionsMeteo entry. Check data consistency.")
            # df_fait.dropna(subset=['id_dim_condition'], inplace=True)
        df_fait = df_fait.drop(columns=['code_condition', 'texte_condition'])
        print(f"INFO: After DimConditionsMeteo merge. Records with id_dim_condition: {df_fait['id_dim_condition'].notna().sum()}/{len(df_fait)}.")


        # Merge with DimTemps to get id_dim_temps_fk
        print("INFO: Merging with DimTemps to get id_dim_temps_fk...")
        # Drop rows where datetime_observation was coerced to NaT BEFORE merging with DimTemps
        initial_rows_before_time_dropna = len(df_fait)
        df_fait = df_fait.dropna(subset=['datetime_observation', 'temp_date', 'temp_annee', 'temp_mois', 'temp_jour', 'temp_heure', 'temp_minute'])
        if len(df_fait) < initial_rows_before_time_dropna:
             print(f"WARNING: Dropped {initial_rows_before_time_dropna - len(df_fait)} rows due to unparseable datetime_observation for DimTemps merge.")

        df_fait = pd.merge(df_fait, df_dim_temps_target,
                           left_on=['temp_date', 'temp_annee', 'temp_mois', 'temp_jour', 'temp_heure', 'temp_minute'],
                           right_on=['date', 'annee', 'mois', 'jour', 'heure', 'minute'],
                           how='left',
                           suffixes=('_fact', '_dim_temps'))

        missing_temps_fks = df_fait['id_dim_temps'].isna().sum()
        if missing_temps_fks > 0:
            print(f"WARNING: {missing_temps_fks} records in FaitDonneesMeteo could not find a matching DimTemps entry. Check data consistency.")
            # df_fait.dropna(subset=['id_dim_temps'], inplace=True) # Consider dropping rows with unmatchable time

        print(f"INFO: After DimTemps merge. Records with id_dim_temps: {df_fait['id_dim_temps'].notna().sum()}/{len(df_fait)}.")


        # Select relevant columns for FaitDonneesMeteo
        # Ensure all FK columns are non-null before final selection if NOT NULL constraints are strict
        # For 'id_dim_lieu_fk' etc. if they are not nullable in the DB,
        # you MUST dropna(subset=['id_dim_lieu', 'id_dim_temps', 'id_dim_condition']) BEFORE this step.
        df_fait_final: pd.DataFrame = df_fait[[
            'id_dim_lieu', 'id_dim_temps', 'id_dim_condition',
            'temperature_celsius', 'vent_kph', 'vent_degre', 'direction_vent',
            'pression_millibars', 'precipitation_mm', 'humidite_pourcentage',
            'nuages_pourcentage', 'visibilite_km', 'indice_uv', 'rafales_kph'
        ]].rename(columns={
            'id_dim_lieu': 'id_dim_lieu_fk',
            'id_dim_temps': 'id_dim_temps_fk',
            'id_dim_condition': 'id_dim_condition_fk'
        })

        # Final check for any remaining NaNs in foreign key columns before loading
        # If the database columns are NOT NULL, rows with NaN here will cause the error.
        fks_to_check = ['id_dim_lieu_fk', 'id_dim_temps_fk', 'id_dim_condition_fk']
        initial_final_rows = len(df_fait_final)
        df_fait_final.dropna(subset=fks_to_check, inplace=True)
        if len(df_fait_final) < initial_final_rows:
            print(f"WARNING: Dropped {initial_final_rows - len(df_fait_final)} rows from final fact table due to NULL foreign keys.")
            print("         Consider adjusting merge logic or source data to prevent missing dimension matches.")


        print(f"SUCCESS: Transformed {len(df_fait_final)} rows for FaitDonneesMeteo (after final FK check).")

        # --- 5. Load Fact Table to Target DB ---
        print("\nINFO: Loading fact data into target database.")
        # Use target_engine (SQLAlchemy) for loading the fact table
        load_dataframe_to_db(df_fait_final, target_engine, 'FaitDonneesMeteo', if_exists_option='append')
        print("SUCCESS: Fact table loaded.")

        print("\nSUCCESS: ETL process completed successfully!")

    except Exception as e:
        print(f"CRITICAL ERROR: An error occurred during the ETL process: {e}")
    finally:
        # --- Close Connections ---
        print("INFO: Attempting to close database connections and dispose of engines.")
        if source_conn:
            source_conn.close()
            print("INFO: Source database connection closed.")
        if target_conn:
            target_conn.close()
            print("INFO: Target database (pymysql) connection closed.")
        if target_engine: # Dispose of the SQLAlchemy engine
            target_engine.dispose()
            print("INFO: Target database SQLAlchemy engine disposed.")
        print("SUCCESS: All database connections and engines handled.")
        
        
if __name__ == "__main__":
    transform_load_to_warehouse()
    print("INFO: ETL process script completed. Check logs for details.")