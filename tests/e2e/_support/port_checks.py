"""Portable port-conflict detection for E2E tests.

Detects rogue Python processes listening on the same port as the Docker
API container, which would silently intercept HTTP requests and cause
mysterious 404 errors (the two processes have separate in-memory stores).

Works on Windows, macOS, and Linux.  Prefers ``psutil`` when available;
falls back to OS-specific CLI tools (``netstat``, ``lsof``, ``ss``).
All fallbacks are best-effort: if a tool is missing or the user lacks
permissions, the check is silently skipped.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass

import pytest

# ── Optional psutil import ──────────────────────────────────────────

try:
    import psutil
except ImportError:
    psutil = None

# ── Data model ──────────────────────────────────────────────────────

_PYTHON_NAMES = frozenset(
    {
        "python",
        "python.exe",
        "python3",
        "python3.exe",
        "pythonw",
        "pythonw.exe",
    }
)

_RUN_KWARGS = {
    "capture_output": True,
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
    "timeout": 5,
    "check": False,
}


@dataclass(frozen=True)
class Listener:
    """A process listening on a TCP port."""

    pid: int
    name: str


# ── Discovery backends ──────────────────────────────────────────────


def _discover_psutil(port: int) -> list[Listener]:
    """Use *psutil* to find listeners on *port*."""
    if psutil is None:
        return []
    listeners: list[Listener] = []
    for conn in psutil.net_connections(kind="tcp"):
        if conn.status == "LISTEN" and conn.laddr.port == port:
            try:
                proc = psutil.Process(conn.pid)
                listeners.append(Listener(pid=conn.pid, name=proc.name()))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    return listeners


def _discover_windows(port: int) -> list[Listener]:
    """Windows fallback: ``netstat -ano`` + ``tasklist``."""
    result = subprocess.run(["netstat", "-ano"], **_RUN_KWARGS)  # type: ignore[call-overload]
    if result.returncode != 0:
        return []

    pids: set[int] = set()
    for line in result.stdout.splitlines():
        if f":{port}" in line and "LISTENING" in line:
            parts = line.split()
            pid_str = parts[-1] if parts else ""
            if pid_str.isdigit():
                pids.add(int(pid_str))

    listeners: list[Listener] = []
    for pid in pids:
        proc = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
            **_RUN_KWARGS,  # type: ignore[call-overload]
        )
        name = "unknown"
        for csv_line in proc.stdout.splitlines():
            stripped = csv_line.strip().strip('"')
            if stripped and stripped[0] != "I":  # skip header
                name = stripped.split('"')[0]
                break
        listeners.append(Listener(pid=pid, name=name))
    return listeners


def _discover_macos(port: int) -> list[Listener]:
    """macOS fallback: ``lsof``."""
    if not shutil.which("lsof"):
        return []
    result = subprocess.run(
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
        **_RUN_KWARGS,  # type: ignore[call-overload]
    )
    if result.returncode != 0:
        return []

    listeners: list[Listener] = []
    seen: set[int] = set()
    for line in result.stdout.splitlines()[1:]:  # skip header
        parts = line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            pid = int(parts[1])
            if pid not in seen:
                seen.add(pid)
                listeners.append(Listener(pid=pid, name=parts[0]))
    return listeners


def _discover_linux(port: int) -> list[Listener]:
    """Linux fallback: ``ss -ltnp`` (or ``netstat -ltnp``)."""
    cmd: list[str] = []
    if shutil.which("ss"):
        cmd = ["ss", "-ltnp"]
    elif shutil.which("netstat"):
        cmd = ["netstat", "-ltnp"]
    if not cmd:
        return []

    result = subprocess.run(cmd, **_RUN_KWARGS)  # type: ignore[call-overload]
    if result.returncode != 0:
        return []

    return _parse_linux_output(result.stdout, port)


def _parse_linux_output(output: str, port: int) -> list[Listener]:
    """Parse ``ss`` or ``netstat`` output for listeners on *port*."""
    import re

    listeners: list[Listener] = []
    seen: set[int] = set()
    for line in output.splitlines():
        if f":{port}" not in line:
            continue
        # ss format: users:(("python3",pid=1234,...))
        for match in re.finditer(r'"([^"]+)",pid=(\d+)', line):
            name, pid_str = match.group(1), match.group(2)
            pid = int(pid_str)
            if pid not in seen:
                seen.add(pid)
                listeners.append(Listener(pid=pid, name=name))
        # netstat format: 1234/python3
        for match in re.finditer(r"(\d+)/(\S+)", line):
            pid_str, name = match.group(1), match.group(2)
            pid = int(pid_str)
            if pid not in seen:
                seen.add(pid)
                listeners.append(Listener(pid=pid, name=name))
    return listeners


# ── Unified discovery ───────────────────────────────────────────────


def _discover_listeners(port: int) -> list[Listener]:
    """Return processes listening on *port*, best-effort."""
    # Prefer psutil (cross-platform, reliable)
    listeners = _discover_psutil(port)
    if listeners:
        return listeners

    # OS-specific fallbacks
    system = platform.system()
    if system == "Windows":
        return _discover_windows(port)
    if system == "Darwin":
        return _discover_macos(port)
    if system == "Linux":
        return _discover_linux(port)
    return []


# ── Public API ──────────────────────────────────────────────────────


def _is_python_process(name: str) -> bool:
    """Check if *name* looks like a Python interpreter."""
    return name.lower() in _PYTHON_NAMES


def _kill_hint(listeners: list[Listener]) -> str:
    """Build a platform-appropriate kill command hint."""
    pids = " ".join(str(entry.pid) for entry in listeners)
    if platform.system() == "Windows":
        parts = " /PID ".join(str(entry.pid) for entry in listeners)
        return f"taskkill /F /PID {parts}"
    return f"kill -9 {pids}"


def check_port_clean(port: int = 8000) -> None:
    """Fail the test session if a rogue Python process listens on *port*.

    A leftover local Flask/Gradio process on the host intercepts requests
    that should reach the Docker container, causing silent 404 errors
    because the two processes keep separate in-memory stores.

    This is a best-effort check: if the OS tools are unavailable or the
    user lacks permissions, the function returns silently.
    """
    try:
        listeners = _discover_listeners(port)
        python_listeners = [
            entry for entry in listeners if _is_python_process(entry.name)
        ]
        if python_listeners:
            desc = ", ".join(
                f"{entry.name} (PID {entry.pid})" for entry in python_listeners
            )
            hint = _kill_hint(python_listeners)
            pytest.fail(
                f"Port conflict: local Python process(es) on port {port}: "
                f"{desc}. These will intercept API requests meant for Docker. "
                f"Kill them with: {hint}"
            )
    except Exception:  # pragma: no cover
        pass  # best-effort: never break on detection failure
