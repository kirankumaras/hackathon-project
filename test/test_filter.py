# Test type: Integration Test
# Validation: Ensure filter marks transactions inside k-period as valid and outside as invalid
# Command: pytest test/test_filter.py

import pytest
from app.main import filter_transactions, FilterRequest, SimpleTransaction, Period

def test_filter_in_k_period():
    req = FilterRequest(
        transactions=[{"date": "2021-10-01 20:15:00", "amount": 1519}],
        k=[Period(start="2021-10-01 00:00:00", end="2021-10-31 23:59:59")],
        q=[],
        p=[],
        wage=50000
    )
    result = filter_transactions(req)
    assert any(tx.get("inKPeriod") for tx in result["valid"])

def test_filter_outside_k_period():
    req = FilterRequest(
        transactions=[{"date": "2021-11-01 20:15:00", "amount": 1519}],
        k=[Period(start="2021-10-01 00:00:00", end="2021-10-31 23:59:59")],
        q=[],
        p=[],
        wage=50000
    )
    result = filter_transactions(req)
    assert any("does not fall" in tx["message"] for tx in result["invalid"])