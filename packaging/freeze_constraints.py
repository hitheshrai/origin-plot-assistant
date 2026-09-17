"""Run from the validated clean environment; writes dependency versions, no paths."""
import importlib.metadata
from pathlib import Path

root = Path(__file__).resolve().parents[1]
excluded = {'origin-plot-assistant', 'pip', 'setuptools', 'wheel'}
items = {d.metadata['Name'].lower().replace('_', '-'): d.version for d in importlib.metadata.distributions()}
lines = ['# Windows CPython 3.11 clean-install validation, 2026-09-17.']
lines.extend(f'{name}=={version}' for name, version in sorted(items.items()) if name not in excluded)
(root/'packaging/constraints.txt').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print(f'Recorded {len(lines)-1} runtime dependency versions.')
