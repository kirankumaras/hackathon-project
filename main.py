from fastapi import FastAPI, Query
import numpy as np

app = FastAPI(title="Hacking India 26: Advanced Retirement Engine")

# Asset DNA: [Risk, Return, Tax_Save, Liquidity, Expense_Ratio]
ASSET_DB = {
    "NPS (Pension)": [0.2, 0.10, 1.0, 0.1, 0.01],
    "Nifty 50 ETF": [0.6, 0.13, 0.4, 0.9, 0.05],
    "Gold (SGB)": [0.4, 0.09, 0.7, 0.6, 0.02],
    "Fixed Deposit": [0.1, 0.06, 0.0, 0.8, 0.00],
    "Crypto (BTC)": [1.0, 0.25, 0.0, 1.0, 0.15]
}

@app.get("/simulate-roundup")
def simulate(transaction_amount: float, period: int = 20, risk_val: float = 0.5):
    # 1. Roundup Logic
    rounded = np.ceil(transaction_amount / 10) * 10
    savings = round(rounded - transaction_amount, 2)
    
    # 2. Diversification Algorithm
    allocations = {}
    total_suitability = 0
    for name, attr in ASSET_DB.items():
        risk_match = 1 - abs(attr[0] - risk_val)
        time_factor = attr[2] if period > 10 else attr[3] # Tax vs Liquidity
        score = (risk_match * 0.5) + (time_factor * 0.5) - attr[4]
        allocations[name] = max(score, 0.1)
        total_suitability += allocations[name]

    # 3. Final Portfolio & Real Value Calculation
    portfolio = {k: round((v/total_suitability) * savings, 2) for k, v in allocations.items()}
    nominal_future = savings * (1 + 0.10)**period # Avg 10% return
    real_future = nominal_future / (1 + 0.06)**period # 6% Inflation adj
    
    return {
        "saved_today": f"₹{savings}",
        "diversification": portfolio,
        "projection": {
            "period_years": period,
            "future_nominal_value": round(nominal_future, 2),
            "purchasing_power_today": round(real_future, 2)
        },
        "message": "By automating micro-savings, you beat inflation and secure retirement."
    }
