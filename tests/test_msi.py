import pytest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'pipeline'))
import scoring_config

def test_weights_sum_to_one():
    total_weight = (
        scoring_config.WEIGHT_VELOCITY +
        scoring_config.WEIGHT_TICKET +
        scoring_config.WEIGHT_REFUND +
        scoring_config.WEIGHT_DECLINE +
        scoring_config.WEIGHT_CHURN +
        scoring_config.WEIGHT_SEASONAL
    )
    assert abs(total_weight - 1.0) < 0.001, "Weights must sum to exactly 1.0"

def test_threshold_config():
    assert scoring_config.MSI_WATCH_THRESHOLD < scoring_config.MSI_ELEVATED_THRESHOLD
    assert scoring_config.MSI_ELEVATED_THRESHOLD < scoring_config.MSI_CRITICAL_THRESHOLD

def test_msi_subscore_normalization():
    # Helper logic representing what msi_calculator does
    def normalize(val):
        return min(max(val * scoring_config.NORMALIZATION_MULTIPLIER, 0), 100)
        
    assert normalize(-10) == 0  # No negative stress
    assert normalize(0) == 0    # No stress
    assert normalize(25) == 50  # 25% drop -> 50 subscore
    assert normalize(60) == 100 # Capped at 100
