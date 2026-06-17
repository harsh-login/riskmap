INSERT INTO geo_risk_zones (city, region, merchant_count, avg_msi, critical_count, elevated_count, risk_tier, flagged_at)
SELECT 
    m.city,
    MAX(m.region) as region,
    COUNT(DISTINCT m.merchant_id) as merchant_count,
    0 as avg_msi,
    0 as critical_count,
    0 as elevated_count,
    'normal' as risk_tier,
    CURDATE() as flagged_at
FROM merchants m
GROUP BY m.city
ON DUPLICATE KEY UPDATE 
    merchant_count = VALUES(merchant_count);
