import os
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

def get_db_connection():
    load_dotenv()
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        database=os.getenv('DB_NAME', 'contagionmap_db'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def execute_sql_file(cursor, filepath):
    with open(filepath, 'r') as file:
        sql_commands = file.read().split(';')
        for command in sql_commands:
            if command.strip():
                cursor.execute(command)

def load_data():
    print("[load_to_db] Connecting to database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Load merchants
    print("[load_to_db] Loading merchants...")
    merchants_df = pd.read_csv('data/sample_merchants.csv')
    
    # Clear existing data first
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE contagion_events;")
    cursor.execute("TRUNCATE TABLE merchant_network;")
    cursor.execute("TRUNCATE TABLE merchant_health;")
    cursor.execute("TRUNCATE TABLE transactions;")
    cursor.execute("TRUNCATE TABLE geo_risk_zones;")
    cursor.execute("TRUNCATE TABLE merchants;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    merchant_data = [tuple(x) for x in merchants_df.values]
    merchant_query = """
        INSERT INTO merchants (merchant_id, name, category, city, region, franchise_group, tenure_years, card_acceptance_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    # Fix NaNs for franchise_group
    merchant_data = [tuple(None if pd.isna(item) else item for item in row) for row in merchant_data]
    
    cursor.executemany(merchant_query, merchant_data)
    print(f"  {cursor.rowcount} rows inserted.")
    
    # 2. Load transactions
    print("[load_to_db] Loading transactions...")
    txns_df = pd.read_csv('data/sample_transactions.csv')
    txn_data = [tuple(x) for x in txns_df.values]
    
    # Fix NaNs for decline_reason
    txn_data = [tuple(None if pd.isna(item) else item for item in row) for row in txn_data]
    
    txn_query = """
        INSERT INTO transactions (txn_id, merchant_id, cardholder_id, amount, status, txn_date, refund_flag, decline_reason)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(txn_query, txn_data)
    print(f"  {cursor.rowcount} rows inserted.")
    
    conn.commit()
    
    # 3. Run merchant_health rollup
    print("[load_to_db] Running merchant_health rollup...")
    execute_sql_file(cursor, 'database/queries/merchant_health.sql')
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM merchant_health")
    print(f"  {cursor.fetchone()[0]} rows created.")
    
    # 4. Derive network edges
    print("[load_to_db] Deriving network edges...")
    execute_sql_file(cursor, 'database/queries/network_edges.sql')
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM merchant_network")
    print(f"  {cursor.fetchone()[0]} edges created.")
    
    # 5. Initialize geo zones
    print("[load_to_db] Initialising geo zones...")
    execute_sql_file(cursor, 'database/queries/geo_aggregation.sql')
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM geo_risk_zones")
    print(f"  {cursor.fetchone()[0]} zones created.")
    
    print("[load_to_db] Complete.")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_data()
