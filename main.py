import time
import psutil
import threading
import os
import math
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict

app = FastAPI(title="Hacking India 26: BlackRock Challenge V1")

# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------

def parse_date(date_str: str) -> datetime:
    """Parse date string into datetime object with validation."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(f"Invalid date-time format or non-existent date: {date_str}")

# ---------------------------------------------------------
# Models based on Challenge Specs
# ---------------------------------------------------------

class Period(BaseModel):
    start: str
    end: str
    fixed: Optional[float] = 0.0
    extra: Optional[float] = 0.0

    @validator('start', 'end')
    def validate_dates(cls, v):
        parse_date(v)  # ensures validity
        return v

class SimpleTransaction(BaseModel):
    date: str
    amount: float

class Transaction(BaseModel):
    """Used specifically for Validator  endpoint"""
    date: str
    amount: float
    ceiling: float
    remanent: float

class ValidatorRequest(BaseModel):
    wage: float
    transactions: List[Transaction]

class FilterRequest(BaseModel):
    q: List[Period] = []
    p: List[Period] = []
    k: List[Period] = []
    transactions: List[SimpleTransaction]

class ReturnsRequest(BaseModel):
    """Input structure for NPS and Index returns as per Challenge Doc"""
    age: int
    wage: float
    inflation: float
    q: List[Period] = []
    p: List[Period] = []
    k: List[Period] = []
    transactions: List[SimpleTransaction]

# ---------------------------------------------------------
# Logic Engines
# ---------------------------------------------------------

def calculate_tax(income: float) -> float:
    """Simplified progressive tax calculation."""
    if income <= 700000:
        return 0
    tax = 0
    curr = income
    if curr > 1500000:
        tax += (curr - 1500000) * 0.30
        curr = 1500000
    if curr > 1200000:
        tax += (curr - 1200000) * 0.20
        curr = 1200000
    if curr > 1000000:
        tax += (curr - 1000000) * 0.15
        curr = 1000000
    if curr > 700000:
        tax += (curr - 700000) * 0.10
    return tax


def compute_ceiling_and_remanent(expenses: List[SimpleTransaction]) -> List[Transaction]:
    return [
        Transaction(
            date=e.date,
            amount=e.amount,
            ceiling=float(math.ceil(e.amount / 100) * 100),
            remanent=round((math.ceil(e.amount / 100) * 100) - e.amount, 2)
        )
        for e in expenses
    ]

def validate_and_enrich_transactions(
    transactions: List[SimpleTransaction],
    wage: float = 0.0
) -> Dict[str, List[Dict]]:
    """
    Validates transactions:
    - Negative amounts not allowed
    - Duplicate transactions not allowed
    - Total remanent across all transactions must not exceed 10% of wage
    Enriches with ceiling/remanent values.
    """
    valid, invalid, seen = [], [], set()

    enriched = compute_ceiling_and_remanent(transactions)

    # Rule: total remanent must not exceed 10% of wage
    max_remanent = wage * 0.10 if wage > 0 else float("inf")
    total_remanent = sum(tx.remanent for tx in enriched)

    for tx in enriched:
        key = (tx.date, tx.amount)

        if tx.amount < 0:
            invalid.append({**tx.dict(), "message": "Negative amounts are not allowed"})
        elif key in seen:
            invalid.append({**tx.dict(), "message": "Duplicate transaction"})
        else:
            seen.add(key)
            valid.append(tx)

    # If total remanent exceeds wage threshold, mark all as invalid
    if total_remanent > max_remanent:
        invalid.extend([{**tx.dict(), "message": f"Total remanent {total_remanent} exceeds 10% of wage ({max_remanent})"} for tx in valid])
        valid = []

    return {"valid": valid, "invalid": invalid}


def process_remanent_logic(tx_date: str, tx_amount: float, q_list: List[Period], p_list: List[Period]) -> float:
    """Applies Q override and P addition logic for remanent (returns only)."""
    tx_dt = datetime.strptime(tx_date, "%Y-%m-%d %H:%M:%S")

    # Step 1: Rounding
    ceiling = math.ceil(tx_amount / 100) * 100
    rem = round(ceiling - tx_amount, 2)

    # Step 2: Q Override (latest start wins)
    matching_q = [q for q in q_list if datetime.strptime(q.start, "%Y-%m-%d %H:%M:%S") <= tx_dt <= datetime.strptime(q.end, "%Y-%m-%d %H:%M:%S")]
    if matching_q:
        matching_q.sort(key=lambda x: x.start, reverse=True)
        rem = matching_q[0].fixed

    # Step 3: P Addition
    for p in p_list:
        if datetime.strptime(p.start, "%Y-%m-%d %H:%M:%S") <= tx_dt <= datetime.strptime(p.end, "%Y-%m-%d %H:%M:%S"):
            rem += p.extra

    return rem
# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------


@app.post("/blackrock/challenge/v1/transactions:parse")
def parse_transactions(expenses: List[SimpleTransaction]):
    """Parse transactions into ceiling and remanent values using shared logic."""
    return compute_ceiling_and_remanent(expenses)

@app.post("/blackrock/challenge/v1/transactions:validator")
def validate_transactions(req: ValidatorRequest):
    result = validate_and_enrich_transactions(
        [SimpleTransaction(date=tx.date, amount=tx.amount) for tx in req.transactions],
        wage=req.wage 
    )
    return result

@app.post("/blackrock/challenge/v1/transactions:filter")
def filter_transactions(req: FilterRequest):
    # Step 1: Validate and enrich transactions
    result = validate_and_enrich_transactions([
        SimpleTransaction(date=tx.date, amount=tx.amount)
        for tx in req.transactions
    ])

    valid, invalid = [], result["invalid"]

    # Step 2: Apply k-period filtering to valid transactions
    for tx in result["valid"]:
        tx_dt = parse_date(tx.date)
        in_k = any(parse_date(k.start) <= tx_dt <= parse_date(k.end) for k in req.k)

        if in_k:
            valid.append({**tx.dict(), "inKPeriod": True})
        else:
            invalid.append({**tx.dict(), "message": "Transaction does not fall within any k-period"})

    return {"valid": valid, "invalid": invalid}


def calculate_returns(req: ReturnsRequest, rate: float, is_nps: bool):
    # Step 1: Validate and enrich transactions (basic rounding first)
    validation_result = validate_and_enrich_transactions([
        SimpleTransaction(date=tx.date, amount=tx.amount)
        for tx in req.transactions
    ])
    valid_transactions = validation_result["valid"]

    # Step 2: Apply k-period filtering + Q/P remanent logic
    filtered_transactions = []
    for tx in valid_transactions:
        tx_dt = parse_date(tx.date)
        if any(parse_date(k.start) <= tx_dt <= parse_date(k.end) for k in req.k):
            rem = process_remanent_logic(tx.date, tx.amount, req.q, req.p)
            filtered_transactions.append(
                Transaction(
                    date=tx.date,
                    amount=tx.amount,
                    ceiling=tx.ceiling,
                    remanent=rem
                )
            )

    # Step 3: Compute returns
    processed_txs = []
    total_ceiling = sum(tx.ceiling for tx in filtered_transactions)
    years = 60 - req.age if req.age < 60 else 5
    annual_income = req.wage * 12

    for tx in filtered_transactions:
        processed_txs.append({
            "dt": parse_date(tx.date),
            "rem": tx.remanent
        })

    savings_by_dates = []
    for k in req.k:
        k_s, k_e = parse_date(k.start), parse_date(k.end)
        k_sum = sum(t['rem'] for t in processed_txs if k_s <= t['dt'] <= k_e)

        nominal_fv = k_sum * ((1 + rate) ** years)
        real_fv = nominal_fv / ((1 + (req.inflation / 100)) ** years)

        tax_benefit = 0
        if is_nps:
            deduction = min(k_sum, 0.10 * annual_income, 200000)
            tax_benefit = calculate_tax(annual_income) - calculate_tax(annual_income - deduction)

        savings_by_dates.append({
            "start": k.start,
            "end": k.end,
            "amount": round(k_sum, 2),
            "profit": round(real_fv - k_sum, 2),
            "taxBenefit": round(tax_benefit, 2)
        })

    return {
        "transactionsTotalAmount": sum(tx.amount for tx in valid_transactions),
        "transactionsTotalCeiling": total_ceiling,
        "savingsByDates": savings_by_dates
    }

@app.post("/blackrock/challenge/v1/returns:nps")
def nps_returns(req: ReturnsRequest):
    return calculate_returns(req, 0.0711, True)

@app.post("/blackrock/challenge/v1/returns:index")
def index_returns(req: ReturnsRequest):
    return calculate_returns(req, 0.1449, False)

@app.get("/blackrock/challenge/v1/performance")
def performance():
    """Report system performance metrics."""
    proc = psutil.Process(os.getpid())
    return {
        "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "memory": f"{proc.memory_info().rss / (1024 * 1024):.2f} MB",
        "threads": threading.active_count(),
        "cpu": proc.cpu_percent(interval=0.1)
    }