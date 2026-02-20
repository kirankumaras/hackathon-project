from fastapi import FastAPI
import numpy as np

app = FastAPI(title="Hacking India 26: Retirement Engine")

@app.get("/simulate-roundup")
def simulate(transaction_amount: float, risk_value: float = 0.5):
    rounded = np.ceil(transaction_amount / 10) * 10
    savings = round(rounded - transaction_amount, 2)
    return {"saved": savings, "invested_on_port": 5477}
