import pandas as pd
import mysql.connector
import os
from datetime import datetime
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

def run_geo_clustering():
    print("[geo_clustering] Updating geographic zones...")
    conn = get_db_connection()
    
    # Get latest month data
    query = """
        SELECT m.city, mh.msi_score, mh.stress_flag
        FROM merchant_health mh
        JOIN merchants m ON mh.merchant_id = m.merchant_id
        WHERE mh.month_year = (SELECT MAX(month_year) FROM merchant_health)
    """
    df = pd.read_sql(query, conn)
    
    # Aggregate
    geo_stats = df.groupby('city').agg(
        avg_msi=('msi_score', 'mean'),
        critical_count=('stress_flag', lambda x: (x == 'Critical').sum()),
        elevated_count=('stress_flag', lambda x: (x == 'Elevated').sum())
    ).reset_index()
    
    updates = []
    high_risk = 0
    watch = 0
    normal = 0
    
    for _, row in geo_stats.iterrows():
        city = row['city']
        avg_msi = round(row['avg_msi'], 2)
        c_count = int(row['critical_count'])
        e_count = int(row['elevated_count'])
        
        if c_count >= 3:
            tier = 'high_risk'
            high_risk += 1
        elif e_count >= 5:
            tier = 'watch'
            watch += 1
        else:
            tier = 'normal'
            normal += 1
            
        updates.append((avg_msi, c_count, e_count, tier, datetime.now().strftime('%Y-%m-%d'), city))
        
    cursor = conn.cursor()
    update_query = """
        UPDATE geo_risk_zones
        SET avg_msi = %s, critical_count = %s, elevated_count = %s, risk_tier = %s, flagged_at = %s
        WHERE city = %s
    """
    cursor.executemany(update_query, updates)
    conn.commit()
    
    print("[geo_clustering] Zone update complete.")
    print(f"  High-risk zones : {high_risk}")
    print(f"  Watch zones     : {watch}")
    print(f"  Normal zones    : {normal}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_geo_clustering()
