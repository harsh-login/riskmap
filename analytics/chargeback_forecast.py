import pandas as pd
import mysql.connector
import os
import json
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

def calculate_forecast():
    print("[chargeback_forecast] Connecting to database...")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Update output CSV first to get exposure for all affected merchants
    if os.path.exists('exports/contagion_output.csv'):
        out_df = pd.read_csv('exports/contagion_output.csv')
        
        total_exposure = 0
        
        def compute_cb(row):
            # Base = 60 days of volume
            base = row['avg_ticket'] * row['avg_monthly_volume'] * 2
            severity = row['msi_score'] / 100.0
            
            depth = row['propagation_depth']
            depth_factor = 1.0 if depth == 0 else (0.5 if depth == 1 else (0.25 if depth == 2 else 0.1))
            
            cardholder_factor = min(row['cardholder_count'] / 500.0, 1.0)
            
            cb = base * severity * depth_factor * cardholder_factor
            return round(cb, 2)
            
        out_df['est_chargeback_60d'] = out_df.apply(compute_cb, axis=1)
        out_df.to_csv('exports/contagion_output.csv', index=False)
        total_exposure = out_df['est_chargeback_60d'].sum()
        
    # 2. Update contagion_events table
    cursor.execute("SELECT * FROM contagion_events")
    events = cursor.fetchall()
    
    print(f"[chargeback_forecast] Processing {len(events)} contagion events...")
    max_single_event = 0
    max_single_id = None
    
    for event in events:
        source_id = event['source_merchant_id']
        affected = json.loads(event['affected_merchant_ids'])
        
        # Get source base
        cursor.execute("SELECT txn_volume, avg_ticket, msi_score, cardholder_count FROM merchant_health WHERE merchant_id = %s ORDER BY month_year DESC LIMIT 1", (source_id,))
        source_data = cursor.fetchone()
        
        event_total_cb = 0
        if source_data:
            base = float(source_data['avg_ticket']) * float(source_data['txn_volume']) * 2
            sev = float(source_data['msi_score']) / 100.0
            cf = min(float(source_data['cardholder_count']) / 500.0, 1.0)
            event_total_cb += base * sev * 1.0 * cf
            
        for a in affected:
            m_id = a['merchant_id']
            depth = a['depth']
            cursor.execute("SELECT txn_volume, avg_ticket, msi_score, cardholder_count FROM merchant_health WHERE merchant_id = %s ORDER BY month_year DESC LIMIT 1", (m_id,))
            a_data = cursor.fetchone()
            
            if a_data:
                base = float(a_data['avg_ticket']) * float(a_data['txn_volume']) * 2
                sev = float(a_data['msi_score']) / 100.0
                df = 0.5 if depth == 1 else (0.25 if depth == 2 else 0.1)
                cf = min(float(a_data['cardholder_count']) / 500.0, 1.0)
                event_total_cb += base * sev * df * cf
                
        event_total_cb = round(event_total_cb, 2)
        if event_total_cb > max_single_event:
            max_single_event = event_total_cb
            max_single_id = source_id
            
        cursor.execute("UPDATE contagion_events SET estimated_chargeback_volume = %s WHERE event_id = %s", (event_total_cb, event['event_id']))
        
    conn.commit()
    cursor.close()
    conn.close()
    
    print("[chargeback_forecast] Forecasting complete.")
    if 'total_exposure' in locals():
        print(f"  Total estimated chargeback exposure (60-day) : ${total_exposure:,.2f}")
    print(f"  Highest single-event exposure                : ${max_single_event:,.2f} (Merchant {max_single_id})")

if __name__ == "__main__":
    calculate_forecast()
