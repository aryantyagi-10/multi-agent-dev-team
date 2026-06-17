"""
MCP-style tool layer. Exposes a small, controlled set of tools the agents
may use against an isolated per-job workspace. Each tool validates paths to
prevent escaping the sandbox.
"""
import os
import subprocess
import pathlib

WORKSPACE_ROOT = pathlib.Path("/tmp/agent_workspaces")
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)


def _job_dir(job_id: str) -> pathlib.Path:
    d = WORKSPACE_ROOT / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_path(job_id: str, filename: str) -> pathlib.Path:
    base = _job_dir(job_id).resolve()
    target = (base / filename).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Path traversal blocked")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


# ---- MCP tools ----------------------------------------------------------

def read_file(job_id: str, filename: str) -> str:
    """Read a file from the job workspace."""
    path = _safe_path(job_id, filename)
    if not path.exists():
        return f"[read_file] '{filename}' does not exist yet."
    return path.read_text(encoding="utf-8")


def write_code(job_id: str, filename: str, content: str) -> str:
    """Write code to a file inside the job workspace."""
    path = _safe_path(job_id, filename)
    path.write_text(content, encoding="utf-8")
    return f"[write_code] Wrote {len(content)} bytes to '{filename}'."


def run_unit_tests(job_id: str, test_filename: str = "test_main.py") -> dict:
    """Run pytest inside the workspace and capture stdout/stderr."""
    workdir = _job_dir(job_id)
    try:
        proc = subprocess.run(
            ["python", "-m", "pytest", test_filename, "-q", "--no-header"],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return {"passed": proc.returncode == 0, "output": output.strip()[-4000:]}
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": "[run_unit_tests] Timed out after 60s."}
    except Exception as e:  # noqa: BLE001
        return {"passed": False, "output": f"[run_unit_tests] Error: {e}"}
