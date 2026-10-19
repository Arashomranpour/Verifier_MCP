"""Tests that the MCP server registers and dispatches tools over the protocol layer."""

import json

import pytest

from verifier_mcp.server import mcp

EXPECTED = {"verify_math", "run_code", "validate_schema", "check_units", "test_regex"}


@pytest.mark.asyncio
async def test_all_tools_registered():
    names = {t.name for t in await mcp.list_tools()}
    assert EXPECTED <= names


@pytest.mark.asyncio
async def test_call_tool_returns_structured_content():
    _content, structured = await mcp.call_tool("verify_math", {"expression": "2+2", "claimed_result": "5"})
    assert structured["verified"] is False


@pytest.mark.asyncio
async def test_call_tool_text_content_is_json():
    content, _structured = await mcp.call_tool("check_units", {"expression": "3 meter"})
    payload = json.loads(content[0].text)
    assert payload["ok"] is True
