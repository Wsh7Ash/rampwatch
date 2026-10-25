#!/usr/bin/env python3
"""rampwatch — ramp-up load runs with percentile reporting (loopback by default)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .runner import plan, ramp

console = Console()


@click.group()
@click.version_option()
def main():
    """Plan and run bounded ramp-up load tests against services you own."""


@main.command("plan")
@click.option("--start-rps", default=5, show_default=True, type=int)
@click.option("--step-rps", default=5, show_default=True, type=int)
@click.option("--max-rps", default=25, show_default=True, type=int)
@click.option("--seconds-per-step", default=2.0, show_default=True, type=float)
@click.option("--json-out", is_flag=True, help="Print the plan as JSON.")
def plan_cmd(start_rps, step_rps, max_rps, seconds_per_step, json_out):
    """Show the ramp stages without sending any request."""
    try:
        stages = plan(start_rps, step_rps, max_rps, seconds_per_step)
    except ValueError as exc:
        console.print(f"[red]error:[/red] {exc}")
        sys.exit(2)

    total_requests = sum(s["requests"] for s in stages)
    total_seconds = round(sum(s["seconds"] for s in stages), 3)
    if json_out:
        click.echo(json.dumps({"stages": stages,
                               "total_requests": total_requests,
                               "total_seconds": total_seconds}, indent=2))
        sys.exit(0)

    table = Table(title="Ramp plan")
    for col in ("Stage", "RPS", "Requests", "Seconds"):
        table.add_column(col)
    for s in stages:
        table.add_row(str(s["stage"]), str(s["rps"]),
                      str(s["requests"]), str(s["seconds"]))
    console.print(table)
    console.print(f"{len(stages)} stage(s), {total_requests} request(s), "
                  f"{total_seconds}s total")
    sys.exit(0)


@main.command()
@click.option("--url", default="http://127.0.0.1:8080/", show_default=True,
              help="Target URL (loopback unless --allow-public).")
@click.option("--start-rps", default=5, show_default=True, type=int)
@click.option("--step-rps", default=5, show_default=True, type=int)
@click.option("--max-rps", default=25, show_default=True, type=int)
@click.option("--seconds-per-step", default=2.0, show_default=True, type=float)
@click.option("--allow-public", is_flag=True,
              help="Permit a non-loopback target you are authorized to test.")
@click.option("--output", "-o", default=None, show_default=False,
              type=click.Path(dir_okay=False),
              help="Write the JSON summary to this file.")
@click.option("--json-out", is_flag=True, help="Print only the JSON summary.")
def run(url, start_rps, step_rps, max_rps, seconds_per_step, allow_public,
        output, json_out):
    """Send a bounded ramp-up load run and report latency percentiles."""
    if not json_out:
        console.print(f"ramping {url} "
                      f"{start_rps}->{max_rps} rps (step {step_rps}, "
                      f"{seconds_per_step}s/stage)")
    try:
        summary = ramp(url, start_rps=start_rps, step_rps=step_rps,
                       max_rps=max_rps, seconds_per_step=seconds_per_step,
                       allow_public=allow_public)
    except ValueError as exc:
        console.print(f"[red]error:[/red] {exc}")
        sys.exit(2)

    payload = json.dumps(summary, indent=2)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        if not json_out:
            console.print(f"[green]saved {path}[/green]")
    if json_out:
        click.echo(payload)
    else:
        table = Table(title=f"Results for {url}")
        for col in ("Metric", "Value"):
            table.add_column(col)
        for key in ("requests", "duration_s", "achieved_rps", "p50_ms",
                    "p95_ms", "p99_ms", "min_ms", "max_ms", "mean_ms",
                    "errors", "success_rate"):
            table.add_row(key, str(summary[key]))
        console.print(table)
        console.print("status counts: "
                      + ", ".join(f"{k}:{v}" for k, v in
                                  summary["status_counts"].items()))

    if summary["requests"] == 0 or summary["success_rate"] == 0:
        if not json_out:
            console.print("[red]every request failed[/red]")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
