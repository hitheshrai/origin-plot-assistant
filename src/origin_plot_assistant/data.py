"""CSV validation and recipe preparation; never silently alter measurements."""
import csv
import hashlib
import math
from pathlib import Path

MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 64


def read_table(path: Path) -> tuple[list[str], list[list[str]]]:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('CSV is larger than the 20 MB limit for version 0.1.')
    with path.open('r', encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, strict=True)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError('CSV is empty.') from None
        headers = [v.strip() for v in headers]
        if not 2 <= len(headers) <= MAX_COLUMNS or any(not h or len(h) > 120 for h in headers):
            raise ValueError('CSV needs 2–64 named columns; headers must contain 1–120 characters.')
        if len(headers) != len(set(headers)):
            raise ValueError('CSV column names must be unique.')
        if any(any(ord(c) < 32 for c in h) for h in headers):
            raise ValueError('Column names cannot contain control characters.')
        rows = []
        for line, row in enumerate(reader, 2):
            if len(row) != len(headers):
                raise ValueError(f'CSV row {line} has a different number of fields from the header.')
            rows.append(row)
            if len(rows) > MAX_ROWS:
                raise ValueError('CSV exceeds the 100,000-row limit for version 0.1.')
        if len(rows) < 2:
            raise ValueError('At least two data rows are required.')
    return headers, rows


def inspect_csv(path: Path) -> dict:
    headers, rows = read_table(path)
    numeric = []
    for index, header in enumerate(headers):
        try:
            if all(math.isfinite(float(row[index])) for row in rows):
                numeric.append(header)
        except ValueError:
            pass
    return {'columns': headers, 'numeric_columns': numeric, 'rows': len(rows),
            'raw_values_returned': False}


def safe_label(value: str) -> str:
    if not isinstance(value, str) or len(value) > 120 or any(ord(c) < 32 or c in '\\";$%{}' for c in value):
        raise ValueError('Labels must be at most 120 characters, without control characters or LabTalk escape/substitution characters.')
    return value


def prepare_plot(path: Path, recipe: dict) -> tuple[list[list[float]], dict]:
    if not isinstance(recipe, dict):
        raise ValueError('A plot recipe must be a JSON object.')
    headers, rows = read_table(path)
    x, ys = recipe.get('x_column'), recipe.get('y_columns')
    if x not in headers or not isinstance(ys, list) or not 1 <= len(ys) <= 8:
        raise ValueError('Select an existing X column and 1–8 Y columns.')
    if any(y not in headers or y == x for y in ys) or len(set(ys)) != len(ys):
        raise ValueError('Y columns must be distinct existing columns different from X.')
    if recipe.get('kind', 'line') not in ['line', 'scatter', 'line_scatter']:
        raise ValueError('Plot kind must be line, scatter or line_scatter.')
    for axis in ['x', 'y']:
        if recipe.get(axis + '_scale', 'linear') not in ['linear', 'log10']:
            raise ValueError('Axis scale must be linear or log10.')
    selected = [headers.index(h) for h in [x, *ys]]
    values = []
    for line, row in enumerate(rows, 2):
        try:
            numbers = [float(row[index]) for index in selected]
        except ValueError:
            raise ValueError(f'Selected columns contain a missing or nonnumeric value at row {line}.') from None
        if not all(math.isfinite(v) for v in numbers):
            raise ValueError(f'Selected columns contain a nonfinite value at row {line}.')
        if recipe.get('x_scale') == 'log10' and numbers[0] <= 0:
            raise ValueError('Logarithmic X requires strictly positive values.')
        if recipe.get('y_scale') == 'log10' and any(v <= 0 for v in numbers[1:]):
            raise ValueError('Logarithmic Y requires strictly positive values.')
        values.append(numbers)
    cleaned = {'schema_version': 1, 'x_column': x, 'y_columns': ys,
        'kind': recipe.get('kind', 'line'), 'x_scale': recipe.get('x_scale', 'linear'),
        'y_scale': recipe.get('y_scale', 'linear'),
        'x_label': safe_label(recipe.get('x_label') or x),
        'y_label': safe_label(recipe.get('y_label') or (ys[0] if len(ys) == 1 else 'Value')),
        'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    for name in [x, *ys]:
        safe_label(name)
    return values, cleaned
