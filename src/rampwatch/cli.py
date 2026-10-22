#!/usr/bin/env python3
import click, json
from pathlib import Path
from rich.console import Console
from .runner import ramp
console = Console()
@click.group()
@click.version_option()
def main(): pass
@main.command()
@click.option('--url', default='http://127.0.0.1:8080/', help='Local target URL')
@click.option('--max-rps', default=25)
@click.option('--output', '-o', default='results/rampwatch.json')
def run(url, max_rps, output):
    res = ramp(url, max_rps=max_rps)
    console.print(res)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(res, indent=2))
    console.print(f'[green]saved {output}[/green]')
if __name__ == '__main__': main()
