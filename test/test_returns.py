# Test type: Functional Test
# Validation: Ensure returns endpoint applies Q override and P addition correctly
# Command: pytest test/test_returns.py

import pytest
from app.main import calculate_returns, ReturnsRequest, SimpleTransaction, Period

def test_returns_with_q_and_p_logic():
    req = ReturnsRequest(
        transactions=[{"date": "2021-10-01 20:15:00", "amount": 1519}],
        k=[Period(start="2021-10-01 00:00:00", end="2021-10-31 23:59:59")],
        q=[Period(start="2021-10-01 00:00:00", end="2021-10-15 23:59:59", fixed=50)],
        p=[Period(start="2021-10-01 00:00:00", end="2021-10-31 23:59:59", extra=20)],
        wage=50000,
        age=30,
        inflation=5
    )
    result = calculate_returns(req, rate=0.08, is_nps=False)
    assert result["savingsByDates"][0]["amount"] == 70  # fixed=50 + extra=20