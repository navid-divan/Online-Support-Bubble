from __future__ import annotations

import datetime as _dt
import functools
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import os
import sys
import tracemalloc

try:
    import resource
except ImportError:
    resource = None

_MEM_MODE = os.environ.get("OSB_PROFILE_MEM", "rss")

TIME_LOG = "time_log"
SPACE_LOG = "space_log"


@dataclass
class _Stat:
    name: str
    calls: int = 0
    cum_time: float = 0.0
    self_time: float = 0.0
    cum_rss: int = 0
    self_rss: int = 0


_stats: dict[str, _Stat] = {}
_stack: list[list] = []
_enabled = False
_patched: list[tuple] = []


def _rss() -> int:
    if resource is None:
        return 0
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def _measure() -> int:
    if _MEM_MODE == "tracemalloc":
        return tracemalloc.get_traced_memory()[0]
    return _rss()


def profile(name: str | None = None) -> Callable:
    def decorate(fn: Callable) -> Callable:
        label = name or f"{fn.__module__}.{fn.__qualname__}"

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not _enabled:
                return fn(*args, **kwargs)
            child = [0.0, 0]
            _stack.append(child)
            start_t, start_r = time.perf_counter(), _measure()
            try:
                return fn(*args, **kwargs)
            finally:
                dt = time.perf_counter() - start_t
                dr = max(0, _measure() - start_r)
                _stack.pop()
                stat = _stats.get(label)
                if stat is None:
                    stat = _Stat(label)
                    _stats[label] = stat
                stat.calls += 1
                stat.cum_time += dt
                stat.self_time += dt - child[0]
                stat.cum_rss += dr
                stat.self_rss += max(0, dr - child[1])
                if _stack:
                    _stack[-1][0] += dt
                    _stack[-1][1] += dr

        wrapper._osb_profiled = True
        return wrapper

    return decorate


def _wrap_module(module: Any, names: list[str]) -> None:
    for name in names:
        original = getattr(module, name, None)
        if original is None or getattr(original, "_osb_profiled", False):
            continue
        _patched.append((module, name, original))
        setattr(module, name, profile(f"{module.__name__}.{name}")(original))


def _instrument_crypto() -> None:
    from osb.crypto import as_scheme, be_scheme, gs_scheme
    from osb.crypto.primitives import schnorr

    _wrap_module(as_scheme, ["setup", "keygen", "derive_pk", "derive_sk", "check", "sign", "verify"])
    _wrap_module(gs_scheme, ["keygen", "join", "sign", "verify", "revoke", "trace"])
    _wrap_module(be_scheme, ["setup", "encrypt", "decrypt"])
    _wrap_module(schnorr, ["sign", "verify"])


def _restore() -> None:
    for module, name, original in _patched:
        setattr(module, name, original)
    _patched.clear()


def run_and_log(
    operation: Callable[[], Any],
    label: str,
    time_path: str | Path = TIME_LOG,
    space_path: str | Path = SPACE_LOG,
) -> Any:
    global _enabled
    _stats.clear()
    _stack.clear()
    _instrument_crypto()
    if _MEM_MODE == "tracemalloc":
        tracemalloc.start()
    _enabled = True
    try:
        return operation()
    finally:
        _enabled = False
        if _MEM_MODE == "tracemalloc":
            tracemalloc.stop()
        _restore()
        _write_time_log(Path(time_path), label)
        _write_space_log(Path(space_path), label)


def _trim(label: str) -> str:
    return label.split("osb.", 1)[-1] if "osb." in label else label


def _human(num: int) -> str:
    value = float(num)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(value) < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TiB"


def _write_time_log(path: Path, label: str) -> None:
    rows = sorted(_stats.values(), key=lambda s: s.cum_time, reverse=True)
    total = sum(s.self_time for s in rows)
    when = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with path.open("w") as f:
        f.write(f"OSB time_log  -  run: {label}  -  {when}\n")
        f.write("wall-clock seconds per instrumented function; reset every run.\n")
        f.write("cumulative_s includes callees; self_s excludes them.\n\n")
        f.write(f"{'cumulative_s':>14}{'self_s':>12}{'calls':>8}  function\n")
        f.write(f"{'-' * 64}\n")
        for s in rows:
            f.write(f"{s.cum_time:>14.6f}{s.self_time:>12.6f}{s.calls:>8}  {_trim(s.name)}\n")
        f.write(f"\ninstrumented self-time total: {total:.6f} s   ({len(rows)} functions)\n")


def _write_space_log(path: Path, label: str) -> None:
    rows = sorted(_stats.values(), key=lambda s: s.cum_rss, reverse=True)
    when = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with path.open("w") as f:
        metric = (
            "net allocated bytes (tracemalloc)"
            if _MEM_MODE == "tracemalloc"
            else "peak RSS growth (getrusage)"
        )
        f.write(f"OSB space_log  -  run: {label}  -  {when}\n")
        f.write(f"space metric: {metric}; reset every run.\n")
        f.write("cumulative includes callees; self excludes them.\n\n")
        f.write(f"{'cumulative':>14}{'self':>12}{'calls':>8}  function\n")
        f.write(f"{'-' * 64}\n")
        for s in rows:
            f.write(f"{_human(s.cum_rss):>14}{_human(s.self_rss):>12}{s.calls:>8}  {_trim(s.name)}\n")
        f.write(f"\n({len(rows)} functions; peak RSS is monotonic, so totals attribute growth)\n")
