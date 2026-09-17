import argparse
import json
from pathlib import Path
from .doctor import diagnose
from .jobs import create_job, run_worker
from .settings import load_settings, load_key


def main():
    parser = argparse.ArgumentParser(description='Origin Plot Assistant')
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('doctor')
    replay = sub.add_parser('replay', help='Apply a saved recipe without model calls')
    replay.add_argument('--csv', type=Path, required=True)
    replay.add_argument('--recipe', type=Path, required=True)
    replay.add_argument('--output', type=Path, required=True)
    ask = sub.add_parser('ask', help='Create a CSV plot using OpenCode and your configured API')
    ask.add_argument('--csv', type=Path, required=True)
    ask.add_argument('--output', type=Path, required=True)
    ask.add_argument('--prompt', required=True)
    ask.add_argument('--endpoint')
    ask.add_argument('--model')
    ask.add_argument('--token-file', type=Path, help='Optional authentication-only file; otherwise use saved Windows credential')
    args = parser.parse_args()
    if args.command == 'doctor':
        report = diagnose()
        print(json.dumps(report, indent=2))
        return 0 if report['ready'] else 1
    if args.command in ['ask', 'replay']:
        try:
            job = create_job(args.csv, args.output)
            if args.command == 'replay':
                recipe = json.loads(args.recipe.read_text(encoding='utf-8'))
                if recipe.get('schema_version') != 1:
                    raise ValueError('Unsupported recipe version.')
                outcome = {'job': str(job), 'result': run_worker(job, recipe), 'model_calls': 0}
            else:
                from .runner import run_assistant
                settings = load_settings()
                settings['endpoint'] = args.endpoint or settings['endpoint']
                settings['model'] = args.model or settings['model']
                if args.endpoint and not args.token_file and args.endpoint != load_settings()['endpoint']:
                    raise ValueError('Supply the authorized token file when overriding the saved endpoint.')
                provider = (lambda: args.token_file.read_text(encoding='utf-8-sig').strip()) if args.token_file else load_key
                outcome = run_assistant(job, args.prompt, settings, key_provider=provider)
            print(json.dumps(outcome, indent=2))
            return 0 if outcome['result']['status'] == 'passed' else 1
        except (ValueError, RuntimeError, OSError) as exc:
            print(json.dumps({'status': 'failed', 'error': str(exc)}))
            return 1
    from .ui import main as launch
    launch()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
