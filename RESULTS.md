# Results — rampwatch

## Environment
- OS: Windows (msys2 shell), Python 3.14.3
- Runtime: python.exe in a fresh virtualenv
- Dependency manager: pip (`pip install -e .`)

## Validation performed
- install: PASS (exit 0)
- unit tests: PASS (exit 0)
- CLI help: PASS (exit 0)
- CLI plan: PASS (exit 0)
- CLI rejected target (exit 2 expected): PASS (exit 2)
- demo run: PASS (195 lines captured in results/demo-output.txt)
- secret/path scan: PASS (no secrets, no machine-specific paths)

## Commands executed

```shell
-m pip install -q -e .
```
# -> install: exit 0
```shell
-m pytest -q
```
# -> unit tests: exit 0
```shell
rampwatch --help
```
# -> CLI help: exit 0
```shell
rampwatch plan --json-out
```
# -> CLI plan: exit 0
```shell
rampwatch run --url http://example.test/ --start-rps 1 --step-rps 1 --max-rps 1 --seconds-per-step 0.1
```
# -> CLI rejected target (exit 2 expected): exit 2

## Observed result

**install**

```

```

**unit tests**

```
.............                                                            [100%]
13 passed in 4.01s
```

**CLI help**

```
Commands:
  plan  Show the ramp stages without sending any request.
  run   Send a bounded ramp-up load run and report latency percentiles.
```

**CLI plan**

```
  "total_requests": 150,
  "total_seconds": 10.0
}
```

**CLI rejected target (exit 2 expected)**

```
ramping http://example.test/ 1->1 rps (step 1, 0.1s/stage)
error: refusing non-local target example.test; loopback only by default — pass 
--allow-public for a host you are authorized to test
```

## Generated artifacts

- `results/demo-output.txt` — full demo transcript with real exit codes
- `docs/ARCHITECTURE.md`, `docs/USAGE.md`, `docs/PROJECT_SPEC.md`
- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `README.md`

## Known limitations

See the **Limitations** section of `README.md`. In short: single-process scope,
heuristic detection where noted, and advisory output that must be interpreted by
a human who knows the system under test.
