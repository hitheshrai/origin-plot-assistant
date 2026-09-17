"""Exercise the installed package through MCP using only synthetic data."""
import asyncio
import json
import os
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from origin_plot_assistant.jobs import create_job


async def main():
    root = Path(__file__).resolve().parents[1]
    job = create_job(root/'examples/example.csv', root/'package-validation')
    env = {k: os.environ[k] for k in ['SYSTEMROOT','WINDIR','USERPROFILE','APPDATA','LOCALAPPDATA','TEMP','TMP','PROGRAMDATA','PATH','COMSPEC'] if k in os.environ}
    env['ORIGIN_PLOT_JOB'] = str(job)
    params = StdioServerParameters(command=sys.executable, args=['-m', 'origin_plot_assistant.server'], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert [t.name for t in tools.tools] == ['inspect_csv', 'plot_csv']
            info = await session.call_tool('inspect_csv', {})
            assert not info.isError
            output = await session.call_tool('plot_csv', {'x_column': 'Time_s', 'y_columns': ['Signal_A','Signal_B'],
                'x_label': 'Time (s)', 'y_label': 'Signal (a.u.)'})
            assert not output.isError
            result = json.loads(next(c.text for c in output.content if c.type == 'text'))
            assert result['status'] == 'passed', result
            print(json.dumps({'installed_mcp': 'passed', 'result': result, 'job': str(job)}, indent=2))


asyncio.run(main())
