# Usage — rampwatch

## Install

```shell
pip install -e .
```

## Commands

```shell
rampwatch --help
```

## Examples

### Inspect the plan (no traffic)

```shell
rampwatch plan --start-rps 10 --step-rps 10 --max-rps 50
```

### Run against a local target

```shell
rampwatch run --url http://127.0.0.1:8080/ --max-rps 50 -o results/run.json
```

### JSON for a gate

```shell
rampwatch run --url http://127.0.0.1:8080/ --json-out | jq .success_rate
```

### Authorized non-local target

```shell
rampwatch run --url https://staging.myapp.example/ --max-rps 20 --allow-public
```

## Ramp shape

`--start-rps`, `--step-rps`, `--max-rps` define the stages; each stage runs
`round(rps * --seconds-per-step)` requests paced at `1/rps`. A run exits 1 only
when every request failed (e.g. nothing listening), which makes it usable as a
health gate. Results include p50/p95/p99, min/max/mean, achieved RPS, error count
and the status distribution.

## Validation gates

- **install**: `pip install -e . (fresh venv)`
- **unit tests**: `pytest -q (13 tests, includes a live loopback ramp)`
- **CLI smoke**: `rampwatch --help; rampwatch plan`
- **demo run**: `logs/2026-10-25/run_demos.py -> results/demo-output.txt`
- **secret scan**: `no tokens/keys/.env/machine paths in tree`

## Exit codes

- `0` — success / nothing at or above the threshold
- `1` — findings, failures, or an unmet `--require`
- `2` — usage error, unreadable input, or rejected target
