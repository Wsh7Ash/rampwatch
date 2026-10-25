"""Ramp-up load runner with latency percentile reporting.

Safety: targets must be loopback unless `allow_public=True` is passed
explicitly (`--allow-public` on the CLI). There are no flood, amplification
or header-spoofing features — request counts are bounded by the ramp plan.
"""

from __future__ import annotations

import time
from urllib.parse import urlparse

import requests

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "0.0.0.0"}


def check_target(url: str, allow_public: bool = False) -> str:
    """Validate the target URL and return its hostname.

    Raises ValueError for unsupported schemes or non-loopback hosts when
    `allow_public` is False.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported scheme {parsed.scheme!r} (http/https only)")
    host = parsed.hostname or ""
    if not host:
        raise ValueError(f"no hostname in {url!r}")
    if host not in LOOPBACK_HOSTS and not allow_public:
        raise ValueError(
            f"refusing non-local target {host}; loopback only by default — "
            "pass --allow-public for a host you are authorized to test")
    return host


def plan(start_rps: int = 5, step_rps: int = 5, max_rps: int = 25,
         seconds_per_step: float = 2.0) -> list[dict]:
    """Compute the ramp stages without touching the network."""
    if start_rps <= 0 or step_rps <= 0 or max_rps <= 0:
        raise ValueError("rps values must be positive")
    if seconds_per_step <= 0:
        raise ValueError("seconds_per_step must be positive")
    if start_rps > max_rps:
        raise ValueError("start_rps must not exceed max_rps")
    stages = []
    stage_no = 1
    rps = start_rps
    while rps <= max_rps:
        requests_count = max(1, int(round(rps * seconds_per_step)))
        stages.append({
            "stage": stage_no,
            "rps": rps,
            "requests": requests_count,
            "seconds": round(requests_count / rps, 3),
        })
        stage_no += 1
        rps += step_rps
    return stages


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile; 0.0 for an empty sample."""
    if not values:
        return 0.0
    if not 0 <= p <= 100:
        raise ValueError("percentile must be within 0..100")
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(p / 100 * (len(ordered) - 1))))
    return ordered[idx]


def summarize(latencies: list[float], status_counts: dict, elapsed: float) -> dict:
    total = sum(v for v in status_counts.values() if isinstance(v, int))
    errors = status_counts.get("error", 0)
    return {
        "requests": len(latencies),
        "duration_s": round(elapsed, 3),
        "achieved_rps": round(len(latencies) / elapsed, 2) if elapsed > 0 else 0.0,
        "p50_ms": round(percentile(latencies, 50), 2),
        "p95_ms": round(percentile(latencies, 95), 2),
        "p99_ms": round(percentile(latencies, 99), 2),
        "min_ms": round(min(latencies), 2) if latencies else 0.0,
        "max_ms": round(max(latencies), 2) if latencies else 0.0,
        "mean_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "errors": errors,
        "success_rate": round((total - errors) / total, 4) if total else 0.0,
        "status_counts": {str(k): v for k, v in status_counts.items()},
    }


def ramp(url: str, start_rps: int = 5, step_rps: int = 5, max_rps: int = 25,
         seconds_per_step: float = 2.0, allow_public: bool = False,
         timeout: float = 5.0) -> dict:
    """Run the ramp plan against `url` and return the summary dict."""
    check_target(url, allow_public=allow_public)
    stages = plan(start_rps, step_rps, max_rps, seconds_per_step)
    latencies: list[float] = []
    status_counts: dict[str, int] = {}
    started = time.perf_counter()
    for stage in stages:
        interval = 1.0 / stage["rps"]
        for _ in range(stage["requests"]):
            t0 = time.perf_counter()
            try:
                resp = requests.get(url, timeout=timeout)
                code = str(resp.status_code)
            except requests.RequestException:
                code = "error"
            elapsed = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed)
            status_counts[code] = status_counts.get(code, 0) + 1
            sleep_for = interval - (time.perf_counter() - t0)
            if sleep_for > 0:
                time.sleep(sleep_for)
    total_elapsed = time.perf_counter() - started
    summary = summarize(latencies, status_counts, total_elapsed)
    summary["target"] = url
    summary["stages"] = stages
    return summary
