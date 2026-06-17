import pandas as pd
import mysql.connector
import os
from collections import defaultdict
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

def build_network():
    print("[network_builder] Building adjacency list...")
    conn = get_db_connection()
    
    query = "SELECT merchant_a, merchant_b, edge_weight FROM merchant_network"
    df = pd.read_sql(query, conn)
    conn.close()
    
    adjacency_list = defaultdict(list)
    
    for _, row in df.iterrows():
        a = int(row['merchant_a'])
        b = int(row['merchant_b'])
        weight = float(row['edge_weight'])
        
        # Build symmetric graph
        adjacency_list[a].append((b, weight))
        adjacency_list[b].append((a, weight))
        
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/sample_network_edges.csv', index=False)
    
    total_edges = len(df)
    total_nodes = len(adjacency_list)
    avg_edges = total_edges / max(total_nodes, 1)
    
    print("[network_builder] Adjacency list built.")
    print(f"  Nodes (merchants)  : {total_nodes}")
    print(f"  Edges (total)      : {total_edges}")
    print(f"  Avg edges per node : {avg_edges:.1f}")
    print("  Edge CSV exported  : data/sample_network_edges.csv")
    
    return adjacency_list

if __name__ == "__main__":
    build_network()
