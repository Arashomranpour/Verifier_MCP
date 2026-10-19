"""Sandboxed Python execution.

Runs a snippet in a fresh, isolated subprocess (`python -I -S`) with CPU, memory and
output limits and no inherited environment, so an LLM can *run* code to check that it
does what it claims rather than hallucinating the output.

NOTE: this is a lightweight sandbox suitable for a dev tool. For untrusted multi-tenant
use, run it inside a container / gVisor / Firecracker — documented in the README.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from typing import Any

_MAX_OUTPUT = 20_000  # chars


def _limits(cpu_seconds: int, mem_mb: int):
    # Applied in the child before exec (POSIX only).
    def _apply():
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        mem = mem_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))  # no forking
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))  # no file writes

    return _apply


def run_code(code: str, stdin: str = "", timeout: float = 5.0) -> dict[str, Any]:
    """Execute a Python snippet and capture its output.

    Returns {ok, return_code, stdout, stderr, timed_out}. `ok` is True when the process
    exits 0 within the limits.
    """
    preexec = _limits(int(timeout) + 1, 256) if sys.platform != "win32" else None
    try:
        with tempfile.TemporaryDirectory() as cwd:
            proc = subprocess.run(
                [sys.executable, "-I", "-S", "-c", code],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env={"PYTHONHASHSEED": "0"},
                preexec_fn=preexec,
                check=False,
            )
        return {
            "ok": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[:_MAX_OUTPUT],
            "stderr": proc.stderr[:_MAX_OUTPUT],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False, "return_code": None, "timed_out": True,
            "stdout": (exc.stdout or b"").decode("utf-8", "replace")[:_MAX_OUTPUT]
            if isinstance(exc.stdout, bytes) else (exc.stdout or "")[:_MAX_OUTPUT],
            "stderr": f"Timed out after {timeout}s",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "return_code": None, "timed_out": False,
                "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}
