# PROJECT SPEC — rampwatch

| Field | Value |
|---|---|
| Name | `rampwatch` |
| Category | load-testing |
| Target user | Operators sanity-checking their own services under ramping load |
| Problem | Quick load checks usually mean repurposing a general-purpose tool that will happily target anyone's host, and its output buries the percentile that matters. |
| Solution | Plan-then-run ramp testing: `plan` computes stages without traffic, `run` paces requests against loopback (unless --allow-public) and reports p50/p95/p99, achieved RPS and status counts. |
| Core workflow | plan stages -> run against local service -> read percentiles -> tune |
| Stack | Python >=3.10, click, rich |
| Test strategy | tests/test_runner.py covers percentile and plan math, guard rails (remote host, bad scheme, no hostname), summarize arithmetic, a live ramp against an in-process HTTPServer on 127.0.0.1, and CLI exit codes 0/1/2 including JSON output and the required-port path. |
| Demo strategy | `logs/2026-10-25/run_demos.py` runs the real workflow and captures `results/demo-output.txt` with asserted exit codes |
| Safety | Loopback only unless --allow-public is passed explicitly. Request counts are bounded by the ramp plan; there are no flood, amplification, reflection or header-spoofing features. |
| Definition of done | install + pytest + CLI smoke + demo transcript + secret scan all pass; docs (README, ARCHITECTURE, USAGE, CHANGELOG, CONTRIBUTING, SECURITY) present; pushed with green CI |

## Must-have features

- Core workflow end to end: plan stages -> run against local service -> read percentiles -> tune
- Exit-code contract (0/1/2) usable from CI
- `--json-out` machine-readable output where a machine should read it

## Nice-to-have (deferred)

- See README Roadmap.
