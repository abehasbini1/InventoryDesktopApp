import os

import mysql.connector
from dotenv import load_dotenv

# 1. Load env variables
load_dotenv(dotenv_path=".env")

try:
    # 2. Establish connection
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT"),
    )

    if conn.is_connected():
        print("✅ Connected successfully!")

        # 3. Use buffered=True to ensure the cursor is fully loaded and iterable
        cursor = conn.cursor(buffered=True)

        cursor.execute("SHOW DATABASES")

        # 4. Iterating through the cursor
        print("Databases available:")
        for (db_name,) in cursor:
            print(f" - {db_name}")

except mysql.connector.Error as err:
    print(f"❌ Error: {err}")

finally:
    # 5. Always close your connections
    if "conn" in locals() and conn.is_connected():
        cursor.close()
        conn.close()
        print("\nConnection closed.")

# Packaging command:
# python -m PyInstaller --noconfirm --onedir --windowed --add-data "registration.py;." --add-data ".env;." --collect-all customtkinter gui_app.py
