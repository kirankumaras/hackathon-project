# Test type: Unit Test
# Validation: Ensure validator rejects negatives, duplicates, and remanent sum > 10% wage
# Command: pytest test/test_validator.py

import pytest
from app.main import validate_and_enrich_transactions, SimpleTransaction

def test_negative_amount():
    txs = [SimpleTransaction(date="2021-10-01 20:15:00", amount=-500)]
    result = validate_and_enrich_transactions(txs, wage=50000)
    assert len(result["invalid"]) == 1
    assert "Negative amounts" in result["invalid"][0]["message"]

def test_duplicate_transaction():
    txs = [
        SimpleTransaction(date="2021-10-01 20:15:00", amount=500),
        SimpleTransaction(date="2021-10-01 20:15:00", amount=500),
    ]
    result = validate_and_enrich_transactions(txs, wage=50000)
    assert any("Duplicate" in tx["message"] for tx in result["invalid"])

def test_remanent_exceeds_wage_cap():
    txs = [
        SimpleTransaction(date="2021-10-01 20:15:00", amount=9999),
        SimpleTransaction(date="2021-10-02 20:15:00", amount=8888),
    ]
    result = validate_and_enrich_transactions(txs, wage=10000)
    assert len(result["valid"]) == 0
    assert all("exceeds" in tx["message"] for tx in result["invalid"])