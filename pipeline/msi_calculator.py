import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv

import scoring_config

def get_db_connection():
    load_dotenv()
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        database=os.getenv('DB_NAME', 'contagionmap_db'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def calculate_msi():
    print("[msi_calculator] Connecting to database to fetch merchant_health...")
    conn = get_db_connection()
    
    # We fetch merchant categories as well for the seasonal baseline
    query = """
        SELECT mh.*, m.category 
        FROM merchant_health mh
        JOIN merchants m ON mh.merchant_id = m.merchant_id
        ORDER BY mh.merchant_id, mh.month_year
    """
    
    df = pd.read_sql(query, conn)
    
    print(f"[msi_calculator] Scoring {len(df)} merchant-month records...")
    
    # Calculate 3-month trailing averages
    df['txn_volume_3m_avg'] = df.groupby('merchant_id')['txn_volume'].transform(lambda x: x.shift().rolling(window=3, min_periods=1).mean())
    df['avg_ticket_3m_avg'] = df.groupby('merchant_id')['avg_ticket'].transform(lambda x: x.shift().rolling(window=3, min_periods=1).mean())
    df['refund_rate_3m_avg'] = df.groupby('merchant_id')['refund_rate'].transform(lambda x: x.shift().rolling(window=3, min_periods=1).mean())
    df['decline_rate_3m_avg'] = df.groupby('merchant_id')['decline_rate'].transform(lambda x: x.shift().rolling(window=3, min_periods=1).mean())
    df['cardholder_count_3m_avg'] = df.groupby('merchant_id')['cardholder_count'].transform(lambda x: x.shift().rolling(window=3, min_periods=1).mean())
    
    # Category average for the month (Seasonal baseline substitute)
    df['category_seasonal_baseline'] = df.groupby(['category', 'month_year'])['txn_volume'].transform('mean')
    
    msi_updates = []
    
    for idx, row in df.iterrows():
        # Only calculate if we have baseline data, else score is baseline healthy
        if pd.isna(row['txn_volume_3m_avg']):
            msi_score = 10.0 # healthy default
        else:
            # 1. Velocity drop
            velocity_drop_pct = (row['txn_volume_3m_avg'] - row['txn_volume']) / max(row['txn_volume_3m_avg'], 1) * 100
            velocity_subscore = min(max(velocity_drop_pct * scoring_config.NORMALIZATION_MULTIPLIER, 0), 100)
            
            # 2. Average ticket decline
            ticket_decline_pct = (row['avg_ticket_3m_avg'] - row['avg_ticket']) / max(row['avg_ticket_3m_avg'], 1) * 100
            ticket_subscore = min(max(ticket_decline_pct * scoring_config.NORMALIZATION_MULTIPLIER, 0), 100)
            
            # 3. Refund rate spike
            refund_spike_pct = (row['refund_rate'] - row['refund_rate_3m_avg']) * 100 # stored as decimal
            refund_subscore = min(max(refund_spike_pct * scoring_config.NORMALIZATION_MULTIPLIER, 0), 100)
            
            # 4. Decline rate increase
            decline_increase_pct = (row['decline_rate'] - row['decline_rate_3m_avg']) * 100
            decline_subscore = min(max(decline_increase_pct * scoring_config.NORMALIZATION_MULTIPLIER, 0), 100)
            
            # 5. Cardholder churn (Approx using count drop as proxy since we don't have raw IDs)
            churn_pct = (row['cardholder_count_3m_avg'] - row['cardholder_count']) / max(row['cardholder_count_3m_avg'], 1) * 100
            churn_subscore = min(max(churn_pct * scoring_config.NORMALIZATION_MULTIPLIER, 0), 100)
            
            # 6. Seasonal baseline deviation
            seasonal_deviation_pct = (row['category_seasonal_baseline'] - row['txn_volume']) / max(row['category_seasonal_baseline'], 1) * 100
            seasonal_subscore = min(max(seasonal_deviation_pct * scoring_config.NORMALIZATION_MULTIPLIER, 0), 100)
            
            msi_score = (velocity_subscore * scoring_config.WEIGHT_VELOCITY) + \
                        (ticket_subscore * scoring_config.WEIGHT_TICKET) + \
                        (refund_subscore * scoring_config.WEIGHT_REFUND) + \
                        (decline_subscore * scoring_config.WEIGHT_DECLINE) + \
                        (churn_subscore * scoring_config.WEIGHT_CHURN) + \
                        (seasonal_subscore * scoring_config.WEIGHT_SEASONAL)
            
        msi_score = round(msi_score, 2)
        
        if msi_score >= scoring_config.MSI_CRITICAL_THRESHOLD:
            stress_flag = 'Critical'
        elif msi_score >= scoring_config.MSI_ELEVATED_THRESHOLD:
            stress_flag = 'Elevated'
        elif msi_score >= scoring_config.MSI_WATCH_THRESHOLD:
            stress_flag = 'Watch'
        else:
            stress_flag = 'Stable'
            
        msi_updates.append((msi_score, stress_flag, row['category_seasonal_baseline'], row['health_id']))

    # Update Database
    cursor = conn.cursor()
    update_query = """
        UPDATE merchant_health 
        SET msi_score = %s, stress_flag = %s, seasonal_baseline = %s
        WHERE health_id = %s
    """
    cursor.executemany(update_query, msi_updates)
    conn.commit()
    
    # Stats
    df_results = pd.DataFrame(msi_updates, columns=['msi', 'tier', 'baseline', 'id'])
    counts = df_results['tier'].value_counts()
    
    print("[msi_calculator] MSI scoring complete.")
    print(f"  Stable (< {scoring_config.MSI_WATCH_THRESHOLD})   : {counts.get('Stable', 0)} records")
    print(f"  Watch ({scoring_config.MSI_WATCH_THRESHOLD}–{scoring_config.MSI_ELEVATED_THRESHOLD})    : {counts.get('Watch', 0)} records")
    print(f"  Elevated ({scoring_config.MSI_ELEVATED_THRESHOLD}–{scoring_config.MSI_CRITICAL_THRESHOLD}) : {counts.get('Elevated', 0)} records")
    print(f"  Critical ({scoring_config.MSI_CRITICAL_THRESHOLD}+)   : {counts.get('Critical', 0)} records")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    calculate_msi()
