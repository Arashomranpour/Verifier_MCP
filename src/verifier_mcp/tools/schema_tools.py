"""JSON-Schema validation.

Lets an LLM confirm that structured output it produced actually conforms to a schema,
instead of asserting it does.
"""

from __future__ import annotations

import json
from typing import Any

from jsonschema import Draft202012Validator


def _load(value: Any) -> Any:
    return json.loads(value) if isinstance(value, str) else value


def validate_schema(instance: Any, schema: Any) -> dict[str, Any]:
    """Validate a JSON instance against a JSON Schema (Draft 2020-12).

    `instance` and `schema` may be JSON strings or already-parsed objects.
    Returns {valid, errors:[{path, message}]}.
    """
    try:
        inst = _load(instance)
        sch = _load(schema)
    except json.JSONDecodeError as exc:
        return {"valid": False, "errors": [{"path": "", "message": f"invalid JSON: {exc}"}]}

    try:
        validator = Draft202012Validator(sch)
    except Exception as exc:  # noqa: BLE001 - malformed schema
        return {"valid": False, "errors": [{"path": "", "message": f"invalid schema: {exc}"}]}

    errors = []
    for err in sorted(validator.iter_errors(inst), key=lambda e: list(e.path)):
        path = "/".join(str(p) for p in err.path) or "(root)"
        errors.append({"path": path, "message": err.message})

    return {"valid": not errors, "errors": errors}
