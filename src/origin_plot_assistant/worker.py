import json
from pathlib import Path
import sys
from .backend import make_plot


def main():
    job = Path(sys.argv[1]).resolve(strict=True)
    try:
        request = json.loads((job / 'request.json').read_text(encoding='utf-8'))
        result = make_plot(job, request)
    except (ValueError, RuntimeError) as exc:
        result = {'status': 'failed', 'error': str(exc)}
    except Exception as exc:
        # COM errors can contain paths or source text. Keep the public result bounded.
        result = {'status': 'failed', 'error': f'Origin automation failed ({type(exc).__name__}). Check Origin installation, licensing and open dialogs.'}
    (job / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
