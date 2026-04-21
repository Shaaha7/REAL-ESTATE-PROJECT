"""
NEW AGENT: Mortgage Calculator Agent
Drop into: backend/src/agents/mortgage_agent.py
Calculates mortgage payments, affordability, and recommends UAE banks.
"""
from __future__ import annotations
import json
import math
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from loguru import logger

class MortgageRequest(BaseModel):
    property_price_aed: float
    monthly_income_aed: float = 0
    existing_debts_aed: float = 0       # existing monthly debt payments
    down_payment_pct: float = 25.0       # percentage
    interest_rate_pct: float = 4.5
    tenure_years: int = 25
    is_uae_national: bool = False
    is_resident: bool = True

class MortgageAgent:
    def calculate(self, req: MortgageRequest) -> dict:
        # LTV limits
        if not req.is_resident:
            max_ltv = 50.0
        elif req.is_uae_national:
            max_ltv = 80.0 if req.property_price_aed <= 5_000_000 else 70.0
        else:
            max_ltv = 75.0 if req.property_price_aed <= 5_000_000 else 65.0

        actual_down_pct = max(req.down_payment_pct, 100 - max_ltv)
        down_payment = req.property_price_aed * actual_down_pct / 100
        loan_amount = req.property_price_aed - down_payment

        # Monthly mortgage payment
        r = req.interest_rate_pct / 100 / 12
        n = req.tenure_years * 12
        if r == 0:
            monthly_payment = loan_amount / n
        else:
            monthly_payment = loan_amount * (r * (1 + r)**n) / ((1 + r)**n - 1)

        # Affordability
        total_monthly_debt = monthly_payment + req.existing_debts_aed
        dbr = (total_monthly_debt / req.monthly_income_aed * 100) if req.monthly_income_aed > 0 else None
        affordable = dbr <= 50 if dbr else None

        # Closing costs
        dld_fee = req.property_price_aed * 0.04
        agent_commission = req.property_price_aed * 0.02
        mortgage_reg = loan_amount * 0.0025
        valuation_fee = 3000
        total_costs = dld_fee + agent_commission + mortgage_reg + valuation_fee
        total_cash_needed = down_payment + total_costs

        return {
            "property_price_aed": req.property_price_aed,
            "down_payment_aed": round(down_payment),
            "down_payment_pct": round(actual_down_pct, 1),
            "loan_amount_aed": round(loan_amount),
            "monthly_payment_aed": round(monthly_payment),
            "interest_rate_pct": req.interest_rate_pct,
            "tenure_years": req.tenure_years,
            "total_repayment_aed": round(monthly_payment * n),
            "total_interest_aed": round(monthly_payment * n - loan_amount),
            "debt_burden_ratio_pct": round(dbr, 1) if dbr else "Income not provided",
            "uae_central_bank_max_ltv_pct": round(max_ltv, 0),
            "affordable_by_dbr": affordable,
            "closing_costs": {
                "dld_transfer_fee_aed": round(dld_fee),
                "agent_commission_aed": round(agent_commission),
                "mortgage_registration_aed": round(mortgage_reg),
                "valuation_fee_aed": valuation_fee,
                "total_closing_costs_aed": round(total_costs)
            },
            "total_cash_needed_aed": round(total_cash_needed),
            "recommended_banks": [
                "Emirates NBD — from 3.99% fixed",
                "FAB — from 3.89% fixed (competitive for AED 3M+)",
                "ADCB — from 4.15% fixed",
                "Mashreq — good for self-employed",
                "DIB — Islamic Ijara from 4.1%"
            ],
            "note": f"DBR limit is 50% in UAE. Your DBR: {round(dbr,1)}%" if dbr else "Provide monthly income for affordability check"
        }

class MortgageTool(BaseTool):
    name: str = "mortgage_calculator_tool"
    description: str = (
        "Calculates UAE mortgage payments and affordability. "
        "Input JSON: property_price_aed, monthly_income_aed, existing_debts_aed, "
        "down_payment_pct, interest_rate_pct, tenure_years, is_uae_national, is_resident. "
        "Output: monthly payment, DBR, closing costs, total cash needed, bank recommendations."
    )
    agent: MortgageAgent = Field(default_factory=MortgageAgent)
    class Config: arbitrary_types_allowed = True

    def _run(self, s: str) -> str:
        try:
            data = json.loads(s) if isinstance(s, str) else s
            result = self.agent.calculate(MortgageRequest(**data))
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def _arun(self, s: str) -> str:
        return self._run(s)
