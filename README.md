Project Architecture
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
n Layer 1 — Data Generation                    n
n Synthetic merchants, transactions,           n
n distress scenarios (Faker + NumPy)           n
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
                       n
                       t
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
n Layer 2 — SQL Analytics Engine               n
n Merchant health rollups · rolling windows ·  n
n stress flagging · seasonal baselines         n
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
                       n
                       t
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
n Layer 3 — MSI Scoring Engine (Python)        n
n 6-signal Merchant Stress Index ·             n
n watch / elevated / critical tiers            n
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
                       n
                       t
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
n Layer 4 — Network Construction (NetworkX)    n
n Merchant relationship graph ·                n
n shared cardholders · franchise · geography   n
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
                       n
                       t
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
n Layer 5 — Contagion Engine                   n
n BFS propagation · depth rings ·              n
n chargeback forecast regression               n
nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
        

Database Schema — MySQL-- Core tables
merchants         -> merchant_id, name, category, city, region,
                     franchise_group, tenure_years, card_acceptance_date
transactions      -> txn_id, merchant_id, cardholder_id, amount,
                     status, txn_date, refund_flag, decline_reason
merchant_health   -> health_id, merchant_id, month_year, txn_volume,
                     avg_ticket, refund_rate, decline_rate,
                     msi_score, stress_flag-- The novel tables (what makes this unique)
merchant_network  -> edge_id, merchant_a, merchant_b, relationship_type,
                     shared_cardholder_count, edge_weight, last_updated
contagion_events  -> event_id, source_merchant_id, triggered_at,
                     propagation_depth, affected_merchant_ids,
                     estimated_chargeback_volume, severity_level
geo_risk_zones    -> zone_id, city, region, merchant_count,
                     avg_msi, risk_tier, flagged_at


   Python Pipeline — 
Module 1 — Data generator
Faker + Pandas to create 500 merchants, 10,000 transactions, realistic seasonal patterns, and 3 distress scenarios baked
in for the model to detect.
Module 2 — MSI calculator
Weighted formula combining all 6 distress signals into a 0–100 Merchant Stress Index per merchant per month.
Rule-based thresholds flag watch / elevated / critical tiers.
Module 3 — Contagion engine
NetworkX builds the merchant graph; BFS propagates risk scores outward from a distressed node. Output: a propagation
depth map (1-hop, 2-hop, 3-hop exposure).
Module 4 — Chargeback forecaster
Regression model predicting 60-day chargeback volume based on merchant size, distress severity, and historical patterns
from similar collapse events.

riskmap
|
+-- README.md                  
|
+-- docs/
|   
+-- ARCHITECTURE.md         
|   
|   
|   
|   
+-- MSI_METHODOLOGY.md      
+-- DATA_DICTIONARY.md      
+-- POWERBI_GUIDE.md        
<- You are here
<- Full system design
<- Signal weight justification (interview-ready)
<- Every table and column explained
<- Dashboard design and DAX measures
+-- ETHICS_AND_GOVERNANCE.md <- Data ethics, merchant privacy, compliance
|   
+-- INTERVIEW_PREP.md       
|
+-- database/
|   
+-- schema.sql               
|   
|   
|       
+-- seed_data.sql            
+-- queries/
<- Anticipated questions + answers
<- All 6 CREATE TABLE statements
<- 500 merchants + 10k transactions
+-- merchant_health.sql  <- Monthly health rollups
|       
|       
|       
|       
+-- msi_flagging.sql     
+-- network_edges.sql    
<- Stress tier classification
<- Shared cardholder edge derivation
+-- geo_aggregation.sql  <- Regional MSI aggregation
+-- validation_queries.sql <- Sanity + back-test checks
|
+-- pipeline/
|   
+-- generate_data.py         
|   
|   
|   
+-- msi_calculator.py        
+-- network_builder.py       
+-- contagion_engine.py      
|
+-- analytics/
|   
<- Faker-based realistic data generator
<- Merchant Stress Index engine
<- NetworkX graph construction
<- BFS propagation algorithm
+-- chargeback_forecast.py   <- 60-day chargeback regression
|   
+-- geo_clustering.py        
|
+-- tests/
|   
+-- test_msi.py              
|   
|   
+-- test_contagion.py        
+-- test_forecast.py         
|
+-- exports/
|   
+-- contagion_output.csv     
|
+-- powerbi/
|   
+-- ContagionMap.pbix         
|
+-- data/
|   
+-- sample_merchants.csv      
|   
<- Geographic risk zone analysis
<- Unit tests for MSI calculator
<- BFS propagation edge cases
<- Regression sanity tests
<- Final risk scores for Power BI
<- Power BI dashboard file
<- 500-row merchant sample
+-- sample_transactions.csv   <- 10,000-row transaction sample
|   
+-- sample_network_edges.csv  <- 2,400-row edge sample
