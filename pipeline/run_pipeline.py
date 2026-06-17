import os
import sys

# Change working directory to project root so all relative paths
# (data/, database/queries/, exports/) resolve correctly.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(PROJECT_ROOT)

# Add directories to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analytics'))

import generate_data
import load_to_db
import msi_calculator
import network_builder
import contagion_engine
import chargeback_forecast
import geo_clustering

def run_all():
    print("==================================================")
    print("   ContagionMap Pipeline Execution Started")
    print("==================================================")
    
    # Step 0: Data Generation (Optional, run if data doesn't exist or to reset)
    if not os.path.exists('data/sample_merchants.csv') or not os.path.exists('data/sample_transactions.csv'):
        print("\n--- Step 0: Generating Data ---")
        os.makedirs('data', exist_ok=True)
        merchants_df = generate_data.generate_merchants()
        merchants_df.to_csv('data/sample_merchants.csv', index=False)
        txns_df = generate_data.generate_transactions(merchants_df)
        txns_df.to_csv('data/sample_transactions.csv', index=False)
    
    print("\n--- Step 1: Loading Database ---")
    load_to_db.load_data()
    
    print("\n--- Step 2: Calculating MSI ---")
    msi_calculator.calculate_msi()
    
    print("\n--- Step 3: Building Network ---")
    adjacency = network_builder.build_network()
    
    print("\n--- Step 4: Running Contagion Engine ---")
    contagion_engine.run_contagion(adjacency)
    
    print("\n--- Step 5: Chargeback Forecasting ---")
    chargeback_forecast.calculate_forecast()
    
    print("\n--- Step 6: Geographic Clustering ---")
    geo_clustering.run_geo_clustering()
    
    print("\n==================================================")
    print("   Pipeline Execution Complete.")
    print("   Open powerbi/ContagionMap.pbix to view results.")
    print("==================================================")

if __name__ == "__main__":
    run_all()
