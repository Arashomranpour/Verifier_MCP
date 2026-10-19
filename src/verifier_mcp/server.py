"""VerifierMCP — an MCP server that lets any LLM check its own work.

Exposes five verification tools over the Model Context Protocol, built with the official
MCP Python SDK's FastMCP. Run it two ways:

    python -m verifier_mcp.server                 # stdio (Claude Desktop, MCP clients)
    python -m verifier_mcp.server --http          # streamable HTTP on :8000/mcp

The tool bodies live in verifier_mcp.tools so they are unit-testable without the protocol.
"""

from __future__ import annotations

import argparse
from typing import Any

from mcp.server.fastmcp import FastMCP

from verifier_mcp import tools

mcp = FastMCP(
    "verifier-mcp",
    instructions=(
        "Verification tools. Before stating a mathematical result, a regex, structured "
        "JSON, a unit calculation, or what a code snippet outputs, call the matching tool "
        "to CHECK it. Prefer verified facts over asserted ones."
    ),
)


@mcp.tool(description="Verify algebra/calculus symbolically (SymPy). "
          "Pass an equation with '=', or an expression plus claimed_result.")
def verify_math(expression: str, claimed_result: str | None = None) -> dict[str, Any]:
    return tools.verify_math(expression, claimed_result)


@mcp.tool(description="Run a Python snippet in a sandboxed subprocess and return its "
          "stdout/stderr. Use to check that code does what it claims.")
def run_code(code: str, stdin: str = "", timeout: float = 5.0) -> dict[str, Any]:
    return tools.run_code(code, stdin=stdin, timeout=min(timeout, 15.0))


@mcp.tool(description="Validate a JSON instance against a JSON Schema (Draft 2020-12). "
          "Returns validity and a list of errors.")
def validate_schema(instance: Any, schema: Any) -> dict[str, Any]:
    return tools.validate_schema(instance, schema)


@mcp.tool(description="Dimensional analysis (Pint). Evaluate a quantity expression like "
          "'5 meter / second * 2 second'; optionally check it matches expected_unit.")
def check_units(expression: str, expected_unit: str | None = None) -> dict[str, Any]:
    return tools.check_units(expression, expected_unit)


@mcp.tool(description="Test a regex against labelled cases "
          "[{text, should_match}]; returns per-case pass/fail and capture groups.")
def test_regex(pattern: str, cases: list[dict[str, Any]], flags: str = "") -> dict[str, Any]:
    return tools.test_regex(pattern, cases, flags)


def main() -> None:
    parser = argparse.ArgumentParser(description="VerifierMCP server")
    parser.add_argument("--http", action="store_true", help="serve streamable HTTP instead of stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.http:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
