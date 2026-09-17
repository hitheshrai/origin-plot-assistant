"""The model sees two bounded tools, not the filesystem or arbitrary LabTalk."""
import asyncio
import json
import os
from pathlib import Path
from typing import Literal
from mcp.server.fastmcp import FastMCP
from .data import inspect_csv as inspect_table
from .jobs import run_worker


def main():
    job = Path(os.environ['ORIGIN_PLOT_JOB']).resolve(strict=True)
    mcp = FastMCP('origin')
    lock = asyncio.Lock()

    @mcp.tool()
    async def inspect_csv() -> dict:
        """Inspect the CSV selected by the user. Return column names/types and row count, never raw rows."""
        return inspect_table(job / 'input.csv')

    @mcp.tool()
    async def plot_csv(x_column: str, y_columns: list[str],
                       kind: Literal['line', 'scatter', 'line_scatter'] = 'line',
                       x_label: str = '', y_label: str = '',
                       x_scale: Literal['linear', 'log10'] = 'linear',
                       y_scale: Literal['linear', 'log10'] = 'linear') -> dict:
        """Plot selected numeric CSV columns in Origin. Save PNG, PDF, OPJU and a reusable recipe. One plot per job; no data transformations."""
        async with lock:
            recipe = dict(x_column=x_column, y_columns=y_columns, kind=kind,
                          x_label=x_label, y_label=y_label, x_scale=x_scale, y_scale=y_scale)
            try:
                return await asyncio.to_thread(run_worker, job, recipe)
            except ValueError as exc:
                return {'status': 'validation_error', 'error': str(exc)}

    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
