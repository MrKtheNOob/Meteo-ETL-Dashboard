from pymysql import Error

from utils import TABLE_CREATE_STATEMENTS, TABLE_DROP_ORDER, get_db_connection


def execute_query(cursor, query, description=""):
    """Exécute une requête SQL."""
    try:
        if description:
            print(f"--- {description} ---")
        cursor.execute(query)
        cursor.connection.commit()  # Commit the transaction using the connection object
        if description:
            print(f"SUCCESS: {description}")
        return True
    except Error as e:
        print(f"ERROR: Failed to execute '{description}' - {e}")
        return False

def cleanup_and_recreate_db(cursor):
    """Clean up and recreate the database schema."""
    try:
        # Désactiver temporairement la vérification des clés étrangères pour la suppression
        execute_query(cursor, "SET FOREIGN_KEY_CHECKS = 0;", "Disabling foreign key checks")

        # Supprimer les tables dans l'ordre inverse des dépendances
        print("\n--- Dropping existing tables ---")
        for table_name in TABLE_DROP_ORDER:
            query = f"DROP TABLE IF EXISTS {table_name};"
            execute_query(cursor, query, f"Dropping table {table_name}")

        # Réactiver la vérification des clés étrangères
        execute_query(cursor, "SET FOREIGN_KEY_CHECKS = 1;", "Re-enabling foreign key checks")

        # Créer les tables dans le bon ordre de dépendance
        print("\n--- Creating new tables ---")
        for create_statement in TABLE_CREATE_STATEMENTS:
            # Extraire le nom de la table pour la description
            table_name_match = create_statement.split("CREATE TABLE")[1].strip().split(" ")[0]
            execute_query(cursor, create_statement, f"Creating table {table_name_match}")

        print("\nSUCCESS: Database cleanup and recreation completed.")

    except Error as e:
        print(f"ERROR: Unexpected error during cleanup/recreation - {e}")

# --- Point d'entrée du script ---
if __name__ == "__main__":
    print("INFO: Starting database cleanup and recreation script.")
    print("INFO: Ensure the MySQL service is running.")
    print("INFO: Install the PyMySQL connector if not already installed: pip install pymysql")
    print("\nWARNING: This script will delete all data from the specified tables!")
    conn = get_db_connection("meteo")
    if conn is None:
        print("ERROR: Failed to establish database connection.")
    else:
        confirm = input("Do you want to proceed? (yes/no): ").lower()
        if confirm == 'yes':
            cleanup_and_recreate_db(conn.cursor())
        else:
            print("INFO: Operation canceled by the user.")
