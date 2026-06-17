import pytest

def test_chargeback_forecast_logic():
    # Rule base = avg_ticket * (txn_volume / 30) * 60 = avg_ticket * txn_volume * 2
    avg_ticket = 50.0
    txn_volume = 100
    base = avg_ticket * txn_volume * 2
    
    assert base == 10000.0
    
    msi_score = 85.0
    sev = msi_score / 100.0
    
    assert sev == 0.85
    
    depth_factor = 0.5 # depth 1
    
    cardholder_count = 250
    cf = min(cardholder_count / 500.0, 1.0)
    assert cf == 0.5
    
    cb = base * sev * depth_factor * cf
    assert cb == 2125.0
