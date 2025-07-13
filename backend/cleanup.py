from utils import TABLE_CREATE_STATEMENTS, TABLE_DROP_ORDER, connect_mysql


def execute_query(cursor, query, description=""):
    """Executes a SQL query."""
    try:
        if description:
            print(f"--- {description} ---")
        cursor.execute(query)
        cursor.connection.commit()  # Commit the transaction using the connection object
        if description:
            print(f"SUCCESS: {description}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to execute '{description}' - {e}")
        return False

def cleanup_and_recreate_db(cursor):
    """Clean up and recreate the database schema."""
    try:
        # Disable foreign key checks temporarily for cleanup
        execute_query(cursor, "SET FOREIGN_KEY_CHECKS = 0;", "Disabling foreign key checks")

        # Drop tables in reverse dependency order
        print("\n--- Dropping existing tables ---")
        for table_name in TABLE_DROP_ORDER:
            query = f"DROP TABLE IF EXISTS {table_name};"
            execute_query(cursor, query, f"Dropping table {table_name}")

        # Re-enable foreign key checks
        execute_query(cursor, "SET FOREIGN_KEY_CHECKS = 1;", "Re-enabling foreign key checks")

        # Create tables in dependency order
        print("\n--- Creating new tables ---")
        for create_statement in TABLE_CREATE_STATEMENTS:
            # Extract table name for description
            try:
                table_name_match = create_statement.split("CREATE TABLE")[1].strip().split(" ")[0]
                execute_query(cursor, create_statement, f"Creating table {table_name_match}")
            except IndexError:
                print(f"WARNING: Failed to extract table name from statement: {create_statement}")
                continue

        print("\nSUCCESS: Database cleanup and recreation completed.")

    except Exception as e:
        print(f"ERROR: Unexpected error during cleanup/recreation - {e}")

# --- Entry point of the script ---
def main():
    """
    Main function to clean up and recreate the schema.
    """
    db_name = "meteo"
    connection = connect_mysql(db_name)
    if connection:
        try:
            with connection.cursor() as cursor:
                cleanup_and_recreate_db(cursor)
        except Exception as e:
            print(f"ERROR: Failed to clean up and create schema - {e}")
        finally:
            connection.close()

if __name__ == "__main__":
    print("INFO: Starting database cleanup and recreation script.")
    print("INFO: Ensure the MySQL service is running.")
    print("\nWARNING: This script will delete all data from the specified tables!")
    main()
