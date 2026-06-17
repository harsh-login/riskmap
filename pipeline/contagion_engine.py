import pandas as pd
import mysql.connector
import os
import json
from collections import deque
from datetime import datetime
from dotenv import load_dotenv
import scoring_config
from network_builder import build_network

def get_db_connection():
    load_dotenv()
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        database=os.getenv('DB_NAME', 'contagionmap_db'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

DEPTH_DECAY = {1: 1.00, 2: 0.45, 3: 0.18}

def run_contagion(adjacency_list=None):
    if adjacency_list is None:
        adjacency_list = build_network()
        
    conn = get_db_connection()
    
    # Get latest month data for all merchants
    query = """
        SELECT mh.merchant_id, mh.msi_score, mh.stress_flag, m.name, m.city, m.region, m.category, m.franchise_group,
               mh.txn_volume, mh.avg_ticket, mh.refund_rate, mh.decline_rate, mh.cardholder_count
        FROM merchant_health mh
        JOIN merchants m ON mh.merchant_id = m.merchant_id
        WHERE mh.month_year = (SELECT MAX(month_year) FROM merchant_health)
    """
    df_health = pd.read_sql(query, conn)
    merchant_data = df_health.set_index('merchant_id').to_dict('index')
    
    critical_merchants = [m_id for m_id, data in merchant_data.items() if data['stress_flag'] == 'Critical']
    
    print(f"[contagion_engine] Identified {len(critical_merchants)} critical-tier source merchants.")
    print("[contagion_engine] Running BFS propagation...")
    
    events = []
    all_affected_records = []
    
    for source in critical_merchants:
        source_msi = merchant_data[source]['msi_score']
        source_msi_normalised = min(source_msi / 100.0, 1.0)
        
        visited = {source: 0} # tracks min depth
        queue = deque([(source, 0, 1.0)]) # node, depth, cumulative_prob
        
        affected = []
        max_depth_reached = 0
        
        while queue:
            current, depth, prob = queue.popleft()

            if depth > 0:
                affected.append({
                    "merchant_id": current,
                    "depth": depth,
                    "propagation_probability": round(prob, 4)
                })
                max_depth_reached = max(max_depth_reached, depth)

                # Only write to CSV if merchant has health data in the latest month
                if current in merchant_data:
                    record = merchant_data[current].copy()
                    record['merchant_id'] = current
                    record['source_id'] = source
                    record['contagion_risk_score'] = round(prob * 100, 2)
                    record['propagation_depth'] = depth
                    all_affected_records.append(record)

            # Always attempt to propagate neighbors regardless of merchant_data presence
            if depth < scoring_config.CONTAGION_MAX_DEPTH:
                for neighbor, weight in adjacency_list.get(current, []):
                    next_depth = depth + 1

                    if neighbor not in visited or visited[neighbor] > next_depth:
                        visited[neighbor] = next_depth
                        # P(depth d) = source_MSI_normalised * edge_weight * depth_decay_factor(d)
                        new_prob = source_msi_normalised * weight * DEPTH_DECAY.get(next_depth, 0.0)

                        if new_prob > 0.01: # only propagate if meaningful
                            queue.append((neighbor, next_depth, new_prob))
                            
        severity = 'critical' if source_msi >= 90 else 'high'
        
        events.append({
            'source_merchant_id': source,
            'triggered_at': datetime.now(),
            'propagation_depth': max_depth_reached,
            'affected_merchant_ids': json.dumps(affected),
            'severity_level': severity
        })
        
        d1 = sum(1 for a in affected if a['depth'] == 1)
        d2 = sum(1 for a in affected if a['depth'] == 2)
        d3 = sum(1 for a in affected if a['depth'] == 3)
        print(f"  Source {source} -> {len(affected)} merchants affected (depth 1: {d1}, depth 2: {d2}, depth 3: {d3})")
        
    # Write to DB
    if events:
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE contagion_events")
        
        event_query = """
            INSERT INTO contagion_events (source_merchant_id, triggered_at, propagation_depth, affected_merchant_ids, severity_level)
            VALUES (%(source_merchant_id)s, %(triggered_at)s, %(propagation_depth)s, %(affected_merchant_ids)s, %(severity_level)s)
        """
        cursor.executemany(event_query, events)
        conn.commit()
        cursor.close()
        
    # Also write source merchants to output with depth 0
    for source in critical_merchants:
        record = merchant_data[source].copy()
        record['merchant_id'] = source
        record['source_id'] = source
        record['contagion_risk_score'] = 100.0
        record['propagation_depth'] = 0
        all_affected_records.append(record)
        
    # Export CSV for Power BI
    os.makedirs('exports', exist_ok=True)
    if all_affected_records:
        out_df = pd.DataFrame(all_affected_records)
        # Rename for Power BI
        out_df = out_df.rename(columns={
            'name': 'merchant_name',
            'stress_flag': 'stress_tier',
            'txn_volume': 'avg_monthly_volume'
        })
        # Add flagged_at date
        out_df['flagged_at'] = datetime.now().strftime('%Y-%m-%d')
        # Placeholder for chargeback
        out_df['est_chargeback_60d'] = 0.0
        
        # Keep highest risk score if a merchant is affected by multiple sources
        out_df = out_df.sort_values('contagion_risk_score', ascending=False).drop_duplicates('merchant_id')
        out_df.to_csv('exports/contagion_output.csv', index=False)
        
    print("[contagion_engine] Propagation complete.")
    print(f"  Total contagion events written : {len(events)}")
    print(f"  Total merchants affected       : {len(set(a['merchant_id'] for a in all_affected_records if a['propagation_depth'] > 0))} (unique)")
    print("  Output: exports/contagion_output.csv")
    
    conn.close()

if __name__ == "__main__":
    run_contagion()
