"""
ContagionMap — Database Setup Script
Connects to MySQL, creates the database if it doesn't exist, and applies schema.sql.
Run ONCE before the pipeline.
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST     = os.getenv('DB_HOST', 'localhost')
DB_PORT     = int(os.getenv('DB_PORT', 3306))
DB_NAME     = os.getenv('DB_NAME', 'contagionmap_db')
DB_USER     = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'schema.sql')

def main():
    print("=" * 50)
    print("  ContagionMap — Database Setup")
    print("=" * 50)

    # 1. Connect without specifying a database to create it if missing
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except mysql.connector.Error as err:
        print(f"\n[ERROR] Cannot connect to MySQL: {err}")
        print("\nPlease make sure:")
        print("  1. MySQL server is running")
        print("  2. Your credentials in .env are correct")
        sys.exit(1)

    cursor = conn.cursor()

    # 2. Create database
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cursor.execute(f"USE `{DB_NAME}`;")
    print(f"\n[setup_db] Database '{DB_NAME}' ready.")

    # 3. Apply schema — wrap each CREATE TABLE in IF NOT EXISTS
    print("[setup_db] Applying schema...")
    with open(SCHEMA_PATH, 'r') as f:
        raw = f.read()

    # Convert plain CREATE TABLE to CREATE TABLE IF NOT EXISTS
    raw = raw.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ")

    statements = [s.strip() for s in raw.split(';') if s.strip()]
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error as err:
            print(f"  [WARN] {err} — statement skipped")

    conn.commit()
    cursor.close()
    conn.close()

    print("[setup_db] Schema applied successfully.")
    print("\nAll done! You can now run the pipeline:")
    print("  run.bat")
    print("=" * 50)

if __name__ == "__main__":
    main()
