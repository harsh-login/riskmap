import os
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load configuration
load_dotenv()
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 42))

# Initialize Faker and Numpy Random State
np.random.seed(RANDOM_SEED)
fake = Faker()
Faker.seed(RANDOM_SEED)

# Constants
NUM_MERCHANTS = 500
NUM_TRANSACTIONS = 10000
MONTHS_HISTORY = 6
START_DATE = datetime(2023, 10, 1) # 6 months ending March 2024 (as per docs)

CATEGORIES = ['Restaurant', 'Retail', 'Travel', 'Entertainment', 'Healthcare', 'Grocery', 'Fuel', 'Electronics', 'Hospitality', 'Professional Services']
CITIES = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose',
          'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis', 'Seattle', 'Denver', 'Washington']
REGIONS = ['Northeast', 'West', 'Midwest', 'South', 'Southwest']
FRANCHISE_GROUPS = [fake.company() + " Group" for _ in range(50)]

# Mapping Cities to Regions (simplified)
CITY_REGION_MAP = {
    'New York': 'Northeast', 'Philadelphia': 'Northeast', 'Washington': 'Northeast',
    'Los Angeles': 'West', 'San Diego': 'West', 'San Jose': 'West', 'San Francisco': 'West', 'Seattle': 'West',
    'Chicago': 'Midwest', 'Columbus': 'Midwest', 'Indianapolis': 'Midwest',
    'Houston': 'South', 'San Antonio': 'South', 'Dallas': 'South', 'Austin': 'South', 'Fort Worth': 'South', 'Charlotte': 'South', 'Jacksonville': 'South',
    'Phoenix': 'Southwest', 'Denver': 'Southwest'
}

def generate_merchants():
    merchants = []
    
    # Pre-allocate for distress scenarios
    # 47: single collapse, 
    # FastFuel Group (will inject later)
    # Chicago Restaurant Cluster
    
    for i in range(1, NUM_MERCHANTS + 1):
        city = np.random.choice(CITIES)
        region = CITY_REGION_MAP[city]
        
        # Inject scenarios
        if i == 47:
            category = 'Retail'
        elif i in range(100, 108): # FastFuel Group
            category = 'Fuel'
            franchise_group = 'FastFuel Group'
        elif i in range(200, 206): # Chicago Restaurant Cluster
            city = 'Chicago'
            region = CITY_REGION_MAP[city]
            category = 'Restaurant'
            franchise_group = None
        else:
            category = np.random.choice(CATEGORIES)
            franchise_group = np.random.choice(FRANCHISE_GROUPS) if np.random.rand() < 0.4 else None
            
        tenure_years = round(np.random.uniform(0.5, 15.0), 1)
        card_acceptance_date = (START_DATE - timedelta(days=int(tenure_years * 365))).strftime('%Y-%m-%d')
        
        merchants.append({
            'merchant_id': i,
            'name': fake.company(),
            'category': category,
            'city': city,
            'region': region,
            'franchise_group': franchise_group,
            'tenure_years': tenure_years,
            'card_acceptance_date': card_acceptance_date
        })
        
    return pd.DataFrame(merchants)

def generate_transactions(merchants_df):
    transactions = []
    txn_id = 1
    
    # Dates
    dates = [START_DATE + timedelta(days=i) for i in range(182)] # ~6 months
    
    # Generate base transaction counts per merchant to distribute the 10,000 txns
    merchant_base_rates = np.random.poisson(lam=20, size=NUM_MERCHANTS) # baseline txns per month
    
    for month_idx in range(6):
        month_dates = [d for d in dates if (d.month - START_DATE.month) % 12 == month_idx]
        
        for idx, row in merchants_df.iterrows():
            m_id = row['merchant_id']
            base_txns = merchant_base_rates[idx]
            
            # Apply distress scenarios
            refund_prob = 0.03
            decline_prob = 0.05
            
            # Scenario 1: Merchant 47 collapse
            if m_id == 47 and month_idx >= 3:
                base_txns = int(base_txns * (0.8 ** (month_idx - 2))) # Drop volume
                refund_prob = 0.03 + (0.02 * (month_idx - 2)) # Spike refunds
            
            # Scenario 2: FastFuel Group stress (M_IDs 100-107)
            if m_id in range(100, 108) and month_idx >= 4:
                base_txns = int(base_txns * 0.85)
                decline_prob = 0.10
                
            # Scenario 3: Chicago Restaurant Cluster (M_IDs 200-205)
            if m_id in range(200, 206) and month_idx >= 4:
                base_txns = int(base_txns * 0.70)
                
            # Simulate transactions for this month
            num_txns = np.random.poisson(lam=max(base_txns, 1))
            
            for _ in range(num_txns):
                cardholder_id = np.random.randint(1, 2001)
                amount = round(np.random.lognormal(mean=3.5, sigma=0.8), 2)
                amount = max(1.0, amount)
                
                # Determine status
                rand_val = np.random.rand()
                if rand_val < decline_prob:
                    status = 'failed'
                    decline_reason = np.random.choice(['insufficient_funds', 'card_blocked', 'processing_error', 'merchant_limit_exceeded'])
                    refund_flag = 0
                else:
                    status = 'completed'
                    decline_reason = None
                    refund_flag = 1 if np.random.rand() < refund_prob else 0
                    
                txn_date = np.random.choice(month_dates).strftime('%Y-%m-%d')
                
                transactions.append({
                    'txn_id': txn_id,
                    'merchant_id': m_id,
                    'cardholder_id': cardholder_id,
                    'amount': amount,
                    'status': status,
                    'txn_date': txn_date,
                    'refund_flag': refund_flag,
                    'decline_reason': decline_reason
                })
                txn_id += 1
                
    # Sample exactly NUM_TRANSACTIONS if we have too many, or keep what we have
    txns_df = pd.DataFrame(transactions)
    if len(txns_df) > NUM_TRANSACTIONS:
        txns_df = txns_df.sample(n=NUM_TRANSACTIONS, random_state=RANDOM_SEED).sort_values(by='txn_date').reset_index(drop=True)
        txns_df['txn_id'] = txns_df.index + 1
        
    return txns_df

if __name__ == "__main__":
    print("[ContagionMap] Starting data generation...")
    os.makedirs('data', exist_ok=True)
    
    merchants_df = generate_merchants()
    merchants_df.to_csv('data/sample_merchants.csv', index=False)
    
    txns_df = generate_transactions(merchants_df)
    txns_df.to_csv('data/sample_transactions.csv', index=False)
    
    print(f"[ContagionMap] Data generation complete.")
    print(f"  Merchants generated : {len(merchants_df)}")
    print(f"  Transactions generated : {len(txns_df)}")
    print(f"  Distress scenarios injected : 3")
    print(f"  Output: data/sample_merchants.csv")
    print(f"  Output: data/sample_transactions.csv")
