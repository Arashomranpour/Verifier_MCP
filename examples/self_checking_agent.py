"""A self-checking agent: Groq LLM + VerifierMCP tools, connected over real MCP.

The agent is told to *verify before asserting*. It loads the VerifierMCP server's tools
through the Model Context Protocol (langchain-mcp-adapters), binds them to a Groq model,
and solves a problem — calling verify_math / run_code to check itself instead of trusting
its own arithmetic.

    export GROQ_API_KEY=gsk_...                       # real LLM
    python examples/self_checking_agent.py

    python examples/self_checking_agent.py --offline  # no key: scripted reasoning,
                                                       # but the verification is REAL MCP

Run from the repo root.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / "src")

QUESTION = "Is (x+1)^2 equal to x^2 + 1? If not, what is the correct expansion?"

SYSTEM = (
    "You are a careful assistant with verification tools. You must NOT state a mathematical "
    "result without first calling verify_math to check it. Use the tools, then answer."
)


def _client() -> MultiServerMCPClient:
    return MultiServerMCPClient({
        "verifier": {
            "command": sys.executable,
            "args": ["-m", "verifier_mcp.server"],
            "transport": "stdio",
            "env": {"PYTHONPATH": SRC},
        }
    })


async def run_with_groq() -> None:
    from langchain_groq import ChatGroq
    from langgraph.prebuilt import create_react_agent

    tools = await _client().get_tools()
    model = ChatGroq(model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), temperature=0)
    agent = create_react_agent(model, tools, prompt=SYSTEM)

    print(f"\n[Groq] Question: {QUESTION}\n")
    result = await agent.ainvoke({"messages": [("user", QUESTION)]})
    for m in result["messages"]:
        role = m.__class__.__name__.replace("Message", "")
        if getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                print(f"  → tool call: {tc['name']}({tc['args']})")
        elif m.content:
            print(f"  [{role}] {m.content}")
    print()


async def run_offline() -> None:
    """No API key: a scripted 'LLM' makes a wrong claim, then the REAL MCP tool corrects it."""
    tools = {t.name: t for t in await _client().get_tools()}
    verify = tools["verify_math"]

    print(f"\n[offline] Question: {QUESTION}\n")
    claim = "x**2 + 1"
    import json

    def _payload(res) -> dict:
        return json.loads(res[0]["text"] if isinstance(res, list) else str(res))

    print(f'  [Assistant] draft answer: "(x+1)^2 = {claim}"')
    print("  → verify_math((x+1)**2, claimed_result=x**2 + 1)  [real MCP call]")
    res = _payload(await verify.ainvoke({"expression": "(x+1)**2", "claimed_result": claim}))
    print(f"    MCP result: verified={res['verified']}  —  {res['detail']}")

    # The verifier said False, so the agent corrects itself.
    print("  → verify_math((x+1)**2, claimed_result=x**2 + 2*x + 1)  [real MCP call]")
    correct = _payload(await verify.ainvoke({"expression": "(x+1)**2", "claimed_result": "x**2 + 2*x + 1"}))
    print(f"    MCP result: verified={correct['verified']}")
    print('\n  [Assistant] Corrected: (x+1)^2 = x^2 + 2x + 1 — verified, not x^2 + 1.\n')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="run without a Groq key (real MCP, scripted LLM)")
    args = ap.parse_args()
    if args.offline or not os.getenv("GROQ_API_KEY"):
        if not args.offline:
            print("GROQ_API_KEY not set — running --offline (verification is still real MCP).")
        asyncio.run(run_offline())
    else:
        asyncio.run(run_with_groq())


if __name__ == "__main__":
    main()
