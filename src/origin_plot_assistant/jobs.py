"""Local immutable input snapshots and isolated worker execution."""
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from .data import inspect_csv, prepare_plot


def create_job(csv_path: Path, output_root: Path) -> Path:
    csv_path = csv_path.expanduser().resolve(strict=True)
    inspect_csv(csv_path)
    output_root = output_root.expanduser().resolve()
    if any(c in str(output_root) for c in '\";$%{}\r\n'):
        raise ValueError('Choose an output folder without quote, semicolon, dollar, percent or brace characters.')
    job = output_root / (datetime.now().strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
    job.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(csv_path, job / 'input.csv')
    # Validate the actual snapshot, in case the source changed during copying.
    inspect_csv(job / 'input.csv')
    return job


def run_worker(job: Path, recipe: dict) -> dict:
    _, cleaned = prepare_plot(job / 'input.csv', recipe)
    if (job / 'result.json').exists():
        previous = json.loads((job / 'request.json').read_text(encoding='utf-8'))
        if previous != cleaned:
            raise ValueError('This job already ran a different plot. Start a new plotting request.')
        return json.loads((job / 'result.json').read_text(encoding='utf-8'))
    (job / 'request.json').write_text(json.dumps(cleaned, indent=2), encoding='utf-8')
    # pythonw cannot be used for a JSON-returning worker.
    executable = Path(sys.executable)
    if executable.name.lower() == 'pythonw.exe':
        executable = executable.with_name('python.exe')
    try:
        worker = subprocess.run([str(executable), '-m', 'origin_plot_assistant.worker', str(job)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=150)
    except subprocess.TimeoutExpired:
        result = {'status': 'failed', 'error': 'Origin exceeded 150 seconds. Check for an Origin dialog. Its dedicated instance may need to be closed manually.'}
        (job / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        return result
    if (job / 'result.json').exists():
        return json.loads((job / 'result.json').read_text(encoding='utf-8'))
    return {'status': 'failed', 'error': f'Origin worker exited without a result (exit {worker.returncode}).'}
