-- Shared cardholders
INSERT INTO merchant_network (merchant_a, merchant_b, relationship_type, shared_cardholder_count, edge_weight, last_updated)
SELECT 
    t1.merchant_id AS merchant_a,
    t2.merchant_id AS merchant_b,
    'shared_cardholder' AS relationship_type,
    COUNT(DISTINCT t1.cardholder_id) AS shared_cardholder_count,
    LEAST(COUNT(DISTINCT t1.cardholder_id) / 50.0, 1.0) AS edge_weight,
    CURDATE() AS last_updated
FROM transactions t1
JOIN transactions t2 ON t1.cardholder_id = t2.cardholder_id AND t1.merchant_id != t2.merchant_id
GROUP BY t1.merchant_id, t2.merchant_id
HAVING shared_cardholder_count >= 2;

-- Franchise edges
INSERT INTO merchant_network (merchant_a, merchant_b, relationship_type, shared_cardholder_count, edge_weight, last_updated)
SELECT 
    m1.merchant_id AS merchant_a,
    m2.merchant_id AS merchant_b,
    'franchise' AS relationship_type,
    0 AS shared_cardholder_count,
    0.60 AS edge_weight,
    CURDATE() AS last_updated
FROM merchants m1
JOIN merchants m2 ON m1.franchise_group = m2.franchise_group AND m1.merchant_id != m2.merchant_id
WHERE m1.franchise_group IS NOT NULL;

-- Category colocation edges
INSERT INTO merchant_network (merchant_a, merchant_b, relationship_type, shared_cardholder_count, edge_weight, last_updated)
SELECT 
    m1.merchant_id AS merchant_a,
    m2.merchant_id AS merchant_b,
    'category_colocation' AS relationship_type,
    0 AS shared_cardholder_count,
    0.30 AS edge_weight,
    CURDATE() AS last_updated
FROM merchants m1
JOIN merchants m2 ON m1.city = m2.city AND m1.category = m2.category AND m1.merchant_id != m2.merchant_id;

-- Geographic proximity edges
INSERT INTO merchant_network (merchant_a, merchant_b, relationship_type, shared_cardholder_count, edge_weight, last_updated)
SELECT 
    m1.merchant_id AS merchant_a,
    m2.merchant_id AS merchant_b,
    'geographic_proximity' AS relationship_type,
    0 AS shared_cardholder_count,
    0.15 AS edge_weight,
    CURDATE() AS last_updated
FROM merchants m1
JOIN merchants m2 ON m1.city = m2.city AND m1.category != m2.category AND m1.merchant_id != m2.merchant_id;
