"""Symbolic math verification with SymPy.

Lets an LLM check algebra/calculus instead of trusting its own arithmetic:
is an equation actually an identity? Does a claimed result match? What does an
expression simplify or evaluate to?
"""

from __future__ import annotations

from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr


def _parse(expr: str):
    # No implicit multiplication surprises; standard transformations only.
    return parse_expr(expr, evaluate=True)


def verify_math(expression: str, claimed_result: str | None = None) -> dict[str, Any]:
    """Verify a mathematical statement symbolically.

    - If `expression` contains '=', check whether the two sides are equal (an identity).
    - Else if `claimed_result` is given, check whether expression == claimed_result.
    - Else just simplify/evaluate the expression.

    Returns {verified, simplified, numeric, detail}. `verified` is None when there is
    nothing to prove (plain simplification).
    """
    try:
        if "=" in expression and claimed_result is None:
            lhs_s, rhs_s = expression.split("=", 1)
            lhs, rhs = _parse(lhs_s), _parse(rhs_s)
            diff = sp.simplify(lhs - rhs)
            verified = diff == 0
            return {
                "verified": bool(verified),
                "simplified": str(sp.simplify(lhs)),
                "numeric": _num(lhs if verified else diff),
                "detail": "sides are equal" if verified
                else f"not equal; lhs - rhs simplifies to {diff}",
            }

        expr = _parse(expression)
        if claimed_result is not None:
            claimed = _parse(claimed_result)
            diff = sp.simplify(expr - claimed)
            verified = diff == 0
            return {
                "verified": bool(verified),
                "simplified": str(sp.simplify(expr)),
                "numeric": _num(expr),
                "detail": f"expression equals {claimed_result}" if verified
                else f"expression simplifies to {sp.simplify(expr)}, not {claimed_result}",
            }

        simp = sp.simplify(expr)
        return {
            "verified": None,
            "simplified": str(simp),
            "numeric": _num(simp),
            "detail": "simplified (nothing to verify)",
        }
    except Exception as exc:  # noqa: BLE001 - report parse/eval errors to the caller
        return {"verified": False, "error": f"{type(exc).__name__}: {exc}"}


def _num(expr) -> float | None:
    try:
        val = sp.N(expr)
        return float(val) if val.is_number else None
    except (TypeError, ValueError):
        return None
