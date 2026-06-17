INSERT INTO merchant_health (merchant_id, month_year, txn_volume, avg_ticket, refund_rate, decline_rate, cardholder_count)
SELECT 
    merchant_id,
    DATE_FORMAT(txn_date, '%Y-%m') AS month_year,
    COUNT(txn_id) AS txn_volume,
    AVG(amount) AS avg_ticket,
    SUM(refund_flag) / COUNT(txn_id) AS refund_rate,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) / COUNT(txn_id) AS decline_rate,
    COUNT(DISTINCT cardholder_id) AS cardholder_count
FROM transactions
GROUP BY merchant_id, month_year
ON DUPLICATE KEY UPDATE 
    txn_volume = VALUES(txn_volume),
    avg_ticket = VALUES(avg_ticket),
    refund_rate = VALUES(refund_rate),
    decline_rate = VALUES(decline_rate),
    cardholder_count = VALUES(cardholder_count);
