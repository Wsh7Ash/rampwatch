"""Tests for rampwatch: plan math, guard rails, a live loopback run, CLI exits."""

import http.server
import json
import threading

import pytest
from click.testing import CliRunner

from rampwatch.cli import main
from rampwatch.runner import check_target, plan, percentile, ramp, summarize


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep test output quiet
        pass


@pytest.fixture()
def local_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/"
    server.shutdown()
    server.server_close()


# --------------------------------------------------------------- percentile

def test_percentile_nearest_rank():
    assert percentile([1, 2, 3, 4, 5], 50) == 3
    assert percentile([1, 2, 3, 4, 5], 100) == 5
    assert percentile([7], 95) == 7
    assert percentile([], 95) == 0.0
    with pytest.raises(ValueError):
        percentile([1], 101)


# -------------------------------------------------------------------- plan

def test_plan_stages_and_totals():
    stages = plan(5, 5, 25, 2.0)
    assert [s["rps"] for s in stages] == [5, 10, 15, 20, 25]
    assert sum(s["requests"] for s in stages) == 150
    assert stages[0]["requests"] == 10


def test_plan_rejects_bad_input():
    with pytest.raises(ValueError):
        plan(10, 5, 5)          # start > max
    with pytest.raises(ValueError):
        plan(0, 5, 25)          # non-positive
    with pytest.raises(ValueError):
        plan(5, 5, 25, 0)       # zero duration


# ------------------------------------------------------------------- guard

def test_check_target_allows_loopback():
    assert check_target("http://127.0.0.1:8080/") == "127.0.0.1"
    assert check_target("http://localhost:8080/") == "localhost"
    assert check_target("http://example.test/", allow_public=True) == "example.test"


def test_check_target_rejects_remote_and_schemes():
    with pytest.raises(ValueError):
        check_target("http://example.test/")
    with pytest.raises(ValueError):
        check_target("ftp://127.0.0.1/")
    with pytest.raises(ValueError):
        check_target("http:///nohost")


# ---------------------------------------------------------------- summarize

def test_summarize_math():
    out = summarize([10.0, 20.0, 30.0], {"200": 3}, 1.0)
    assert out["requests"] == 3
    assert out["p50_ms"] == 20.0
    assert out["max_ms"] == 30.0
    assert out["errors"] == 0
    assert out["success_rate"] == 1.0
    assert out["achieved_rps"] == 3.0


# -------------------------------------------------------------- live ramp

def test_ramp_against_local_server(local_server):
    summary = ramp(local_server, start_rps=20, step_rps=20, max_rps=40,
                   seconds_per_step=0.2, timeout=5)
    assert summary["requests"] == 12          # 4 + 8
    assert summary["status_counts"]["200"] == 12
    assert summary["errors"] == 0
    assert summary["success_rate"] == 1.0
    assert summary["p95_ms"] >= summary["p50_ms"] >= 0
    assert [s["rps"] for s in summary["stages"]] == [20, 40]


def test_ramp_refuses_remote_without_opt_in():
    with pytest.raises(ValueError):
        ramp("http://example.test/", start_rps=1, step_rps=1, max_rps=1,
             seconds_per_step=0.1)


# -------------------------------------------------------------------- CLI

def test_cli_plan_json():
    res = CliRunner().invoke(main, ["plan", "--start-rps", "5", "--step-rps",
                                    "5", "--max-rps", "25", "--json-out"])
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert payload["total_requests"] == 150
    assert len(payload["stages"]) == 5


def test_cli_plan_bad_input_exits_2():
    res = CliRunner().invoke(main, ["plan", "--start-rps", "10", "--max-rps", "5"])
    assert res.exit_code == 2
    assert "error" in res.output


def test_cli_run_local_writes_output(local_server, tmp_path):
    out = tmp_path / "run.json"
    res = CliRunner().invoke(main, [
        "run", "--url", local_server, "--start-rps", "20", "--step-rps", "20",
        "--max-rps", "20", "--seconds-per-step", "0.2", "-o", str(out)])
    assert res.exit_code == 0, res.output
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["requests"] == 4
    assert payload["status_counts"]["200"] == 4


def test_cli_run_remote_exits_2():
    res = CliRunner().invoke(main, ["run", "--url", "http://example.test/",
                                    "--start-rps", "1", "--step-rps", "1",
                                    "--max-rps", "1", "--seconds-per-step", "0.1"])
    assert res.exit_code == 2
    assert "refusing non-local" in res.output


def test_cli_run_all_failures_exit_1():
    # nothing listens on this loopback port
    res = CliRunner().invoke(main, [
        "run", "--url", "http://127.0.0.1:1/", "--start-rps", "5",
        "--step-rps", "5", "--max-rps", "5", "--seconds-per-step", "0.1",
        "--json-out"])
    assert res.exit_code == 1, res.output
    payload = json.loads(res.output)
    assert payload["status_counts"] == {"error": 1}
