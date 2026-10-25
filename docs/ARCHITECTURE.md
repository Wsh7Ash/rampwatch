# Architecture — rampwatch

## Overview

`rampwatch` (load-testing) is a single-package Python CLI: a `src/rampwatch/` package
with a pure logic module and a Click command layer, console-script entry point
`rampwatch = rampwatch.cli:main`, and no runtime services.

### `src/rampwatch/runner.py`

check_target() enforces the loopback allowlist (http/https only), plan() computes stages purely, percentile()/summarize() are pure math, and ramp() is the single function that opens connections, pacing one request per interval per stage.

### `src/rampwatch/cli.py`

Click group with `plan` and `run` (--url, ramp shape, --allow-public, -o, --json-out). Exits 0 completed, 1 every request failed, 2 rejected target or bad usage.


## Design decisions

- **Logic/rendering separation.** Every decision (classify, parse, lint, plan,
  probe) lives in a pure module with no console output, so tests assert on data
  rather than on terminal formatting.
- **Exit codes as the CI contract.** 0 = clean/success, 1 = findings or failed
  requirement, 2 = usage or read error. `--json-out` switches stdout to
  machine-readable JSON without changing exit codes.
- **Small dependency surface.** Only `click` (CLI), `rich` (tables) and, where
  network I/O is the point, `requests`; everything else is the standard library.

## Data flow

```
input (file / URL / ports + flags)
   -> Click command validates arguments
   -> pure module computes findings / profiles / verdicts / plan
   -> renderer prints table or JSON
   -> process exits 0 / 1 / 2
```

## Testing strategy

tests/test_runner.py covers percentile and plan math, guard rails (remote host, bad scheme, no hostname), summarize arithmetic, a live ramp against an in-process HTTPServer on 127.0.0.1, and CLI exit codes 0/1/2 including JSON output and the required-port path.
