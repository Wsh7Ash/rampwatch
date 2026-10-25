# rampwatch

**Plan and run bounded ramp-up load tests against services you own, with real
latency percentiles — loopback-only unless you explicitly opt in.**

## The problem

You want to know whether the new endpoint still behaves as traffic ramps up.
The obvious tools will happily point thousands of requests at somebody else's
host, and their output buries the number you care about. rampwatch plans the
ramp first, refuses non-local targets by default, and reports p50/p95/p99 plus
status counts from an actual run.

## Features

- **`plan`** — computes stages (`rps`, request count, duration) without
  sending a single packet, so you can sanity-check the shape of a run.
- **`run`** — executes the ramp against a loopback URL, pacing requests to the
  target rate, and reports `p50/p95/p99`, min/max/mean, achieved RPS, error
  count and status distribution.
- **Allowlist guard** — non-loopback targets raise an error unless
  `--allow-public` is passed; there is no flood, amplification or
  header-spoofing mode.
- **Artifacts** — `-o results/rampwatch.json` writes the summary, `--json-out`
  prints it for a gate or a dashboard.
- **Exit codes** — `0` completed with successful requests, `1` every request
  failed, `2` rejected target or bad usage.

## Example output

Real output from `results/demo-output.txt` (30 requests across 3 stages
against `examples/local_target.py`):

```console
$ rampwatch run --url http://127.0.0.1:8080/ --start-rps 20 --step-rps 20 \
      --max-rps 60 --seconds-per-step 0.25 -o results/rampwatch.json
ramping http://127.0.0.1:8080/ 20->60 rps (step 20, 0.25s/stage)
saved results/rampwatch.json
┌──────────────┬───────┐
│ Metric       │ Value │
├──────────────┼───────┤
│ requests     │ 30    │
│ duration_s   │ 0.833 │
│ achieved_rps │ 36.01 │
│ p50_ms       │ 18.82 │
│ p95_ms       │ 39.95 │
│ p99_ms       │ 42.39 │
│ errors       │ 0     │
│ success_rate │ 1.0   │
└──────────────┴───────┘
status counts: 200:30
[exit 0]
```

## Architecture

```
src/rampwatch/
├── runner.py   # check_target(), plan(), percentile(), summarize(), ramp()
└── cli.py      # click: plan/run commands, rendering, exit codes
```

`plan()` and `percentile()` are pure; `ramp()` is the only function that opens
sockets, and it calls `check_target()` first. The test suite runs a real ramp
against an in-process `HTTPServer` on `127.0.0.1`.

## Requirements

- Python 3.10+; `click`, `requests`, `rich` (installed automatically)

## Installation

```shell
git clone https://github.com/Wsh7Ash/rampwatch
cd rampwatch
pip install -e .
```

## Quick start

```shell
# terminal 1 — a local target that ships with the repo
python examples/local_target.py --port 8080

# terminal 2
rampwatch plan
rampwatch run --url http://127.0.0.1:8080/ --max-rps 50
```

## Usage

```shell
# inspect the plan only (no traffic)
rampwatch plan --start-rps 10 --step-rps 10 --max-rps 50 --seconds-per-step 2

# short run with a JSON artifact
rampwatch run --url http://127.0.0.1:8080/health -o results/health.json

# JSON on stdout for a gate
rampwatch run --url http://127.0.0.1:8080/ --json-out | jq .success_rate

# a host you are authorized to test
rampwatch run --url https://staging.myapp.example/ --max-rps 20 --allow-public
```

## Configuration

| Option | Default | Purpose |
| --- | --- | --- |
| `--start-rps` / `--step-rps` / `--max-rps` | `5 / 5 / 25` | ramp shape |
| `--seconds-per-step` | `2.0` | dwell time at each rate |
| `--allow-public` | off | permit a non-loopback target |
| `-o` | none | write the JSON summary to a file |
| `--json-out` | off | print only the JSON summary |

## Testing

```shell
pip install -e . pytest
pytest -q        # 13 tests, includes a live ramp against 127.0.0.1
```

## Project structure

```
rampwatch/
├── src/rampwatch/{runner,cli}.py
├── tests/test_runner.py
├── examples/local_target.py
├── docs/{ARCHITECTURE,USAGE,PROJECT_SPEC}.md
├── results/{rampwatch.json,demo-output.txt}
├── RESULTS.md
└── .github/workflows/ci.yml
```

## Limitations

- Single-connection pacing: it measures your client as much as the server;
  one process is not a distributed load generator.
- GET only, no request bodies, headers or authentication.
- Percentiles use nearest-rank on the sample, which is coarse for very small
  runs.
- The loopback guard is a safety rail, not a policy engine — `--allow-public`
  is a manual promise that you own the target.

## Roadmap

- Concurrent workers per stage with an open-loop scheduler.
- `--duration` mode (run until wall-clock limit instead of a fixed plan).
- Comparing two runs and reporting the delta.

## Security

Only run load against systems you own or are explicitly authorized to test.
`check_target()` refuses non-loopback hosts unless `--allow-public` is given,
and request counts are bounded by the ramp plan. See [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).
