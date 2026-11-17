# finance-engines-mcp

**Deterministic financial math as MCP tools — because LLMs should exercise judgment, not arithmetic.**

[![tests](https://github.com/vmagapu/finance-engines-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/vmagapu/finance-engines-mcp/actions)

## The pattern

Language models are excellent at deciding *when* a calculation is needed and *what the result means* for a user. They are unreliable at the calculation itself — and in financial software, a plausible-but-wrong number is worse than no number.

This server implements the separation I use in production at [MoneyCompass](https://getmoneycompass.com), an AI financial advisor where every number the model presents comes from a deterministic engine layer, never from token prediction:

```
┌─────────────┐     tool call      ┌──────────────────────┐
│   LLM        │ ─────────────────▶ │  finance-engines-mcp  │
│  (judgment:  │                    │  (arithmetic:         │
│   when, why, │ ◀───────────────── │   Decimal, tested,    │
│   so what)   │   exact result +   │   reproducible)       │
└─────────────┘    assumptions      └──────────────────────┘
```

Design rules this repo demonstrates:

- **Pure functions.** No state, no side effects, no network. Same inputs → same outputs, forever.
- **`Decimal` arithmetic.** Money is never represented in binary floating point internally; rounding is explicit (`ROUND_HALF_UP`, cents for money, basis points for rates).
- **Assumptions travel with results.** Every projection returns the assumptions it used, so the model can (and should) disclose them.
- **Schedules reconcile.** The loan engine walks the amortization month by month so totals match to the cent — not just the closed-form payment formula.
- **Errors are errors.** Unreachable goals and invalid inputs raise, rather than returning something plausible.

## Tools

| Tool | What it answers |
|---|---|
| `compound_growth` | "What will my investment be worth?" — monthly compounding + contributions |
| `loan_amortization` | "What does this loan really cost?" — payment, total interest, first/last payment split |
| `effective_annual_rate` | "Which rate is actually better?" — nominal APR → EAR |
| `inflation_adjusted` | "What is that worth in today's dollars?" |
| `savings_goal_months` | "When do I hit my target?" — exact monthly simulation |
| `retirement_projection` | "Will I be ready?" — nominal and real, assumptions disclosed |

## Install & use

```bash
pip install git+https://github.com/vmagapu/finance-engines-mcp
```

**Claude Code:**

```bash
claude mcp add finance-engines -- python -m finance_engines_mcp
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "finance-engines": {
      "command": "python",
      "args": ["-m", "finance_engines_mcp"]
    }
  }
}
```

Then ask: *"If I invest $100k at 7% and add $1,000/month, what's that worth in 20 years — in today's dollars?"* — and watch the model route the arithmetic here instead of guessing.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests pin the engines to independently verifiable reference values (the classic $300k/6%/30yr mortgage at $1,798.65/month, textbook EAR conversions, annuity formulas) plus reconciliation and error-path cases.

## Why so small?

Deliberately. The point is the boundary, not the library: in an agentic system, the interesting engineering is deciding what the model must *not* be allowed to improvise. Everything behind that boundary should be boring, typed, tested code. This repo is the boundary, demonstrated.

— [Vish Magapu](https://vmagapu.github.io) · MIT
