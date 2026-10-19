"""Visual playground for VerifierMCP.

A FastAPI app that calls the same tool functions the MCP server exposes, so you can *see*
each verifier catch an error in the browser:

    uvicorn verifier_mcp.playground:app --port 8080   # open http://localhost:8080

This is a human-facing demo. The actual MCP server is verifier_mcp.server.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from verifier_mcp import tools

WEB_DIR = Path(__file__).resolve().parents[2] / "web"
app = FastAPI(title="VerifierMCP Playground")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    f = WEB_DIR / "index.html"
    return f.read_text(encoding="utf-8") if f.exists() else "<h1>VerifierMCP</h1>"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


class MathReq(BaseModel):
    expression: str
    claimed_result: str | None = None


class CodeReq(BaseModel):
    code: str
    stdin: str = ""


class SchemaReq(BaseModel):
    instance: Any
    schema_json: Any


class UnitsReq(BaseModel):
    expression: str
    expected_unit: str | None = None


class RegexReq(BaseModel):
    pattern: str
    cases: list[dict[str, Any]]
    flags: str = ""


@app.post("/api/verify_math")
def api_math(r: MathReq) -> JSONResponse:
    return JSONResponse(tools.verify_math(r.expression, r.claimed_result))


@app.post("/api/run_code")
def api_code(r: CodeReq) -> JSONResponse:
    return JSONResponse(tools.run_code(r.code, stdin=r.stdin, timeout=5.0))


@app.post("/api/validate_schema")
def api_schema(r: SchemaReq) -> JSONResponse:
    return JSONResponse(tools.validate_schema(r.instance, r.schema_json))


@app.post("/api/check_units")
def api_units(r: UnitsReq) -> JSONResponse:
    return JSONResponse(tools.check_units(r.expression, r.expected_unit))


@app.post("/api/test_regex")
def api_regex(r: RegexReq) -> JSONResponse:
    return JSONResponse(tools.test_regex(r.pattern, r.cases, r.flags))
