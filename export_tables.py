import mysql.connector
import pandas as pd
import os

config = {
    'user': 'root',
    'password': 'nice try',
    'host': 'localhost',
    'database': 'aicanetwork_latest',
}

def export_tables_to_csv():
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
    
        print(f"{[t[0] for t in tables]}")

        for (table_name,) in tables:
            print(f"Exporting {table_name}")
            df = pd.read_sql(f"SELECT * FROM `{table_name}`", conn)
            filename = f"csv/{table_name}.csv"
            df.to_csv(filename, index=False)
            print(f"Saved {filename}")

    except mysql.connector.Error as err:
        print(f"{err}")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    export_tables_to_csv()
