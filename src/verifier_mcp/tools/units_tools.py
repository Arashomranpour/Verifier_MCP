"""Dimensional analysis with Pint.

Catches the classic LLM error of mixing units or producing a physically inconsistent
equation. Evaluate a quantity expression, or check that two sides share dimensions.
"""

from __future__ import annotations

from typing import Any

import pint

_ureg = pint.UnitRegistry()


def check_units(expression: str, expected_unit: str | None = None) -> dict[str, Any]:
    """Evaluate a quantity expression (e.g. '5 meter / second * 2 second').

    Returns {ok, magnitude, units, dimensionality, matches_expected}. If `expected_unit`
    is given, the result is converted to it and `matches_expected` reports compatibility.
    """
    try:
        q = _ureg.parse_expression(expression)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    magnitude = getattr(q, "magnitude", q)
    units = str(getattr(q, "units", "dimensionless"))
    dim = str(getattr(q, "dimensionality", "dimensionless"))

    result: dict[str, Any] = {
        "ok": True,
        "magnitude": float(magnitude) if isinstance(magnitude, (int, float)) else str(magnitude),
        "units": units,
        "dimensionality": dim,
    }
    if expected_unit is not None:
        try:
            converted = q.to(expected_unit)
            result["matches_expected"] = True
            result["as_expected"] = f"{converted:~P}"
        except Exception as exc:  # noqa: BLE001 - incompatible dimensions
            result["matches_expected"] = False
            result["detail"] = f"cannot convert to {expected_unit}: {exc}"
    return result


def units_consistent(lhs: str, rhs: str) -> dict[str, Any]:
    """Check whether both sides of an equation have the same dimensionality."""
    try:
        ql = _ureg.parse_expression(lhs)
        qr = _ureg.parse_expression(rhs)
        same = ql.dimensionality == qr.dimensionality
        return {
            "consistent": bool(same),
            "lhs_dimensionality": str(ql.dimensionality),
            "rhs_dimensionality": str(qr.dimensionality),
        }
    except Exception as exc:  # noqa: BLE001
        return {"consistent": False, "error": f"{type(exc).__name__}: {exc}"}
