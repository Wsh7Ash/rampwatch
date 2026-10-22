import time
import requests
from urllib.parse import urlparse

def check_target(url):
    host = urlparse(url).hostname or ''
    if host not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError(f'refusing non-local target {host}; edit code for authorized remote use')

def percentile(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))
    return s[idx]

def ramp(url, start_rps=5, step_rps=5, max_rps=25, seconds_per_step=2):
    check_target(url)
    latencies = []
    status_counts = {}
    for rps in range(start_rps, max_rps + 1, step_rps):
        n = max(1, int(rps * seconds_per_step))
        interval = 1.0 / rps
        for _ in range(n):
            t0 = time.perf_counter()
            try:
                resp = requests.get(url, timeout=5)
                code = resp.status_code
            except requests.RequestException:
                code = 'error'
            latencies.append((time.perf_counter() - t0) * 1000)
            status_counts[code] = status_counts.get(code, 0) + 1
            time.sleep(max(0.0, interval - (time.perf_counter() - t0)))
    return {
        'requests': len(latencies),
        'p50_ms': round(percentile(latencies, 50), 2),
        'p95_ms': round(percentile(latencies, 95), 2),
        'p99_ms': round(percentile(latencies, 99), 2),
        'status_counts': status_counts,
    }
