"""finance-engines-mcp — deterministic financial math as MCP tools.

Design: the model decides WHEN to calculate and WHAT the numbers mean;
this server decides what the numbers ARE. Tools are pure functions over
Decimal arithmetic — no state, no side effects, no network, no model.
"""

from mcp.server.mcpserver import MCPServer

from . import engines

mcp = MCPServer(
    "finance-engines",
    instructions=(
        "Deterministic financial calculators. Use these tools for ANY financial "
        "arithmetic instead of computing numbers yourself — results are exact, "
        "auditable, and include their assumptions. All rates are annual percentages "
        "(e.g. 7 means 7%). All amounts are in the user's currency units."
    ),
)


@mcp.tool()
def compound_growth(
    principal: float,
    annual_rate_pct: float,
    years: int,
    monthly_contribution: float = 0.0,
) -> dict:
    """Project investment growth with monthly compounding and optional monthly
    contributions. Returns future value, total contributed, total growth, and
    the exact assumptions used."""
    return engines.compound_growth(principal, annual_rate_pct, years, monthly_contribution)


@mcp.tool()
def loan_amortization(principal: float, annual_rate_pct: float, years: int) -> dict:
    """Fixed-rate loan analysis: monthly payment, total paid, total interest,
    and the interest/principal split of the first and last payments. The
    schedule is walked month by month so totals reconcile to the cent."""
    return engines.loan_amortization(principal, annual_rate_pct, years)


@mcp.tool()
def effective_annual_rate(nominal_annual_pct: float, compounds_per_year: int = 12) -> dict:
    """Convert a nominal APR to the effective annual rate (EAR) for a given
    compounding frequency. Use to compare rates quoted with different
    compounding."""
    return engines.effective_annual_rate(nominal_annual_pct, compounds_per_year)


@mcp.tool()
def inflation_adjusted(amount: float, annual_inflation_pct: float, years: int) -> dict:
    """Express a future amount in today's purchasing power given an annual
    inflation rate. Use whenever presenting long-horizon projections so the
    user sees real, not just nominal, values."""
    return engines.inflation_adjusted(amount, annual_inflation_pct, years)


@mcp.tool()
def savings_goal_months(
    target: float,
    current: float,
    annual_rate_pct: float,
    monthly_contribution: float,
) -> dict:
    """How many months until a savings target is reached, simulated month by
    month with growth applied before each contribution. Raises an error if the
    goal is unreachable within 100 years."""
    return engines.savings_goal_months(target, current, annual_rate_pct, monthly_contribution)


@mcp.tool()
def retirement_projection(
    current_age: int,
    retirement_age: int,
    current_savings: float,
    monthly_contribution: float,
    annual_return_pct: float,
    annual_inflation_pct: float = 2.5,
) -> dict:
    """Project retirement savings in both nominal and today's dollars.
    Composes compound growth with inflation adjustment and reports every
    assumption used."""
    return engines.retirement_projection(
        current_age,
        retirement_age,
        current_savings,
        monthly_contribution,
        annual_return_pct,
        annual_inflation_pct,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
