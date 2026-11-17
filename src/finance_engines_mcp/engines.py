"""Deterministic financial calculation engines.

Pure functions, Decimal arithmetic, no side effects, no model in the loop.
Every number an LLM presents to a user should come from code like this —
auditable, testable, and exactly reproducible — never from token prediction.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 28

CENT = Decimal("0.01")
BASIS_POINT = Decimal("0.0001")


def _d(value: float | int | str | Decimal) -> Decimal:
    """Convert via str to avoid float representation error."""
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _rate(value: Decimal) -> Decimal:
    return value.quantize(BASIS_POINT, rounding=ROUND_HALF_UP)


def compound_growth(
    principal: float,
    annual_rate_pct: float,
    years: int,
    monthly_contribution: float = 0.0,
) -> dict:
    """Future value with monthly compounding and end-of-month contributions."""
    if years < 0:
        raise ValueError("years must be >= 0")
    p = _d(principal)
    pmt = _d(monthly_contribution)
    r = _d(annual_rate_pct) / Decimal(100) / Decimal(12)
    n = years * 12

    growth_factor = (Decimal(1) + r) ** n
    fv_principal = p * growth_factor
    if r == 0:
        fv_contributions = pmt * n
    else:
        fv_contributions = pmt * ((growth_factor - Decimal(1)) / r)

    future_value = fv_principal + fv_contributions
    contributed = p + pmt * n
    return {
        "future_value": float(_money(future_value)),
        "total_contributed": float(_money(contributed)),
        "total_growth": float(_money(future_value - contributed)),
        "assumptions": {
            "compounding": "monthly",
            "contribution_timing": "end of month",
            "annual_rate_pct": float(_d(annual_rate_pct)),
            "months": n,
        },
    }


def loan_amortization(principal: float, annual_rate_pct: float, years: int) -> dict:
    """Fixed-rate, fully amortizing loan: payment, totals, first/last split."""
    if years <= 0:
        raise ValueError("years must be > 0")
    p = _d(principal)
    r = _d(annual_rate_pct) / Decimal(100) / Decimal(12)
    n = years * 12

    if r == 0:
        payment = p / n
    else:
        payment = p * r / (Decimal(1) - (Decimal(1) + r) ** Decimal(-n))

    payment = _money(payment)
    first_interest = _money(p * r)
    first_principal = _money(payment - first_interest)

    # Walk the schedule exactly so totals reconcile to the cent.
    balance = p
    total_interest = Decimal(0)
    last_interest = Decimal(0)
    last_principal = Decimal(0)
    for period in range(1, n + 1):
        interest = _money(balance * r)
        principal_part = payment - interest
        if period == n:  # final payment clears residual rounding
            principal_part = balance
        balance -= principal_part
        total_interest += interest
        last_interest, last_principal = interest, principal_part

    return {
        "monthly_payment": float(payment),
        "total_paid": float(_money(payment * (n - 1) + last_principal + last_interest)),
        "total_interest": float(_money(total_interest)),
        "first_payment": {
            "interest": float(first_interest),
            "principal": float(first_principal),
        },
        "last_payment": {
            "interest": float(_money(last_interest)),
            "principal": float(_money(last_principal)),
        },
        "months": n,
    }


def effective_annual_rate(nominal_annual_pct: float, compounds_per_year: int = 12) -> dict:
    """Nominal APR -> effective annual rate (EAR)."""
    if compounds_per_year <= 0:
        raise ValueError("compounds_per_year must be > 0")
    nominal = _d(nominal_annual_pct) / Decimal(100)
    m = Decimal(compounds_per_year)
    ear = (Decimal(1) + nominal / m) ** compounds_per_year - Decimal(1)
    return {
        "nominal_annual_pct": float(_d(nominal_annual_pct)),
        "compounds_per_year": compounds_per_year,
        "effective_annual_pct": float(_rate(ear * Decimal(100))),
    }


def inflation_adjusted(amount: float, annual_inflation_pct: float, years: int) -> dict:
    """Purchasing power of a future amount in today's dollars."""
    if years < 0:
        raise ValueError("years must be >= 0")
    amt = _d(amount)
    i = _d(annual_inflation_pct) / Decimal(100)
    real = amt / ((Decimal(1) + i) ** years)
    return {
        "future_amount": float(_money(amt)),
        "todays_purchasing_power": float(_money(real)),
        "annual_inflation_pct": float(_d(annual_inflation_pct)),
        "years": years,
    }


def savings_goal_months(
    target: float,
    current: float,
    annual_rate_pct: float,
    monthly_contribution: float,
) -> dict:
    """Months until a savings target is reached (exact monthly simulation)."""
    tgt, bal = _d(target), _d(current)
    pmt = _d(monthly_contribution)
    r = _d(annual_rate_pct) / Decimal(100) / Decimal(12)

    if bal >= tgt:
        return {"months": 0, "years_and_months": "0m", "final_balance": float(_money(bal))}
    if pmt <= 0 and r <= 0:
        raise ValueError("goal unreachable: no contributions and no growth")

    months = 0
    while bal < tgt:
        bal = bal * (Decimal(1) + r) + pmt
        months += 1
        if months > 1200:
            raise ValueError("goal not reachable within 100 years")
    return {
        "months": months,
        "years_and_months": f"{months // 12}y {months % 12}m",
        "final_balance": float(_money(bal)),
    }


def retirement_projection(
    current_age: int,
    retirement_age: int,
    current_savings: float,
    monthly_contribution: float,
    annual_return_pct: float,
    annual_inflation_pct: float = 2.5,
) -> dict:
    """Nominal and real (today's dollars) savings at retirement."""
    if retirement_age <= current_age:
        raise ValueError("retirement_age must be greater than current_age")
    years = retirement_age - current_age
    nominal = compound_growth(current_savings, annual_return_pct, years, monthly_contribution)
    real = inflation_adjusted(nominal["future_value"], annual_inflation_pct, years)
    return {
        "years_to_retirement": years,
        "projected_nominal": nominal["future_value"],
        "projected_todays_dollars": real["todays_purchasing_power"],
        "total_contributed": nominal["total_contributed"],
        "assumptions": {
            "annual_return_pct": float(_d(annual_return_pct)),
            "annual_inflation_pct": float(_d(annual_inflation_pct)),
            "compounding": "monthly",
        },
    }
