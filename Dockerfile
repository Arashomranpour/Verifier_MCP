# VerifierMCP — HTTP transport (for remote clients / Amazon Bedrock AgentCore Gateway).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/app/src
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8000
# Streamable HTTP MCP endpoint on :8000/mcp
CMD ["python", "-m", "verifier_mcp.server", "--http", "--host", "0.0.0.0", "--port", "8000"]
