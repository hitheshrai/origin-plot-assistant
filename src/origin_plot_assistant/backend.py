"""Origin COM adapter. Called only inside its dedicated worker process."""
import json
from pathlib import Path
import time
from .data import prepare_plot


def make_plot(job: Path, requested: dict) -> dict:
    import pythoncom
    import win32com.client
    started = time.perf_counter()
    values, recipe = prepare_plot(job / 'input.csv', requested)
    # Output is controlled by the desktop/CLI job, never by an LLM tool argument.
    if any(c in job.as_posix() for c in '\";$%{}\r\n'):
        raise ValueError('Choose an output folder without quote, semicolon, dollar, percent or brace characters.')
    if any((job / ('figure.' + ext)).exists() for ext in ['png', 'pdf', 'opju']):
        raise ValueError('This job already has outputs; create a new job to avoid overwriting them.')
    app = None
    result = {'status': 'failed'}
    pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
    try:
        app = win32com.client.DispatchEx('Origin.Application')
        app.Visible = 0
        app.NewProject()

        def execute(script: str):
            if not app.Execute(script):
                raise RuntimeError('Origin rejected a plotting command. Check the installed Origin version.')

        book = app.CreatePage(2, 'PlotData', 'Origin')
        if not book:
            raise RuntimeError('Origin could not create a worksheet.')
        columns = [recipe['x_column'], *recipe['y_columns']]
        execute(f'win -o {book} {{wks.ncols={len(columns)}; wks.col1.type=4;}}')
        for index, name in enumerate(columns):
            if not app.PutWorksheet(book, [row[index] for row in values], 0, index):
                raise RuntimeError('Origin data transfer failed.')
            execute(f'win -o {book} {{col({index+1})[L]$="{name}";}}')
        back = [list(row) for row in app.GetWorksheet(book, 0, 0, len(values)-1, len(columns)-1)]
        if back != values:
            raise RuntimeError('Origin data verification failed.')
        plot_id = {'line': 200, 'scatter': 201, 'line_scatter': 202}[recipe['kind']]
        execute(f'plotxy iy:=[{book}]1!(1,2:{len(columns)}) plot:={plot_id} ogl:=<new template:=line>;')
        graph = app.ActivePage.Name
        for axis in ['x', 'y']:
            if recipe[axis+'_scale'] == 'log10':
                execute(f'win -o {graph} {{layer.{axis}.type=2;}}')
        execute(f'win -o {graph} {{layer -a;}}')
        for flag, text in [('xb', recipe['x_label']), ('yl', recipe['y_label'])]:
            execute(f'win -o {graph} {{label -{flag} "{text}";}}')
        execute(f'win -o {graph} {{legend -r;}}')
        layer = app.FindGraphLayer(graph)
        if app.GraphPages.Count != 1 or layer is None or layer.DataPlots.Count != len(columns)-1:
            raise RuntimeError('Graph/curve verification failed.')
        layer = None
        for ext in ['png', 'pdf']:
            execute(f'win -o {graph} {{expGraph type:={ext} filename:="figure" '
                    f'path:="{job.as_posix()}" overwrite:=replace;}}')
            if not (job / f'figure.{ext}').exists() or (job / f'figure.{ext}').stat().st_size < 100:
                raise RuntimeError(f'Origin did not create the {ext.upper()} export.')
        if not app.Save(str(job / 'figure.opju')):
            raise RuntimeError('Origin project save failed.')
        app.NewProject()
        if not app.Load(str(job / 'figure.opju')):
            raise RuntimeError('Saved Origin project could not be reopened.')
        back = [list(row) for row in app.GetWorksheet(book, 0, 0, len(values)-1, len(columns)-1)]
        if back != values or app.GraphPages.Count != 1:
            raise RuntimeError('Saved project failed data/graph verification.')
        result = {'status': 'passed', 'rows': len(values), 'series': len(columns)-1,
            'files': ['figure.png', 'figure.pdf', 'figure.opju', 'recipe.json'],
            'checks': {'data_roundtrip': True, 'curve_count': len(columns)-1, 'project_reopen': True}}
        (job / 'recipe.json').write_text(json.dumps(recipe, indent=2), encoding='utf-8')
    finally:
        if app is not None:
            try:
                app.Exit()
                result['origin_closed'] = True
            except Exception:
                result['origin_closed'] = False
            app = None
        pythoncom.CoUninitialize()
    result['elapsed_seconds'] = round(time.perf_counter()-started, 3)
    return result
