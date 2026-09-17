"""HTTPS provider access and an ephemeral credential-isolating local relay."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
import threading
import urllib.error
import urllib.request
from .settings import validate_endpoint


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def list_models(endpoint: str, key: str) -> list[str]:
    endpoint = validate_endpoint(endpoint)
    request = urllib.request.Request(endpoint + '/models',
        headers={'Authorization': 'Bearer ' + key.strip()})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=25) as response:
            data = json.loads(response.read(2_000_000))
    except urllib.error.HTTPError as exc:
        raise ValueError(f'API connection failed (HTTP {exc.code}). Check the endpoint, key and access.') from None
    except Exception:
        raise ValueError('Cannot reach the API. Check the endpoint, network/VPN and key.') from None
    models = sorted({item['id'] for item in data.get('data', []) if isinstance(item, dict) and isinstance(item.get('id'), str)})
    if not models:
        raise ValueError('The API returned no model IDs. Enter an authorized model ID manually if model listing is unsupported.')
    return models


class Relay:
    """No real key is passed to OpenCode or its MCP children."""
    def __init__(self, endpoint: str, model: str, key_provider):
        self.endpoint = validate_endpoint(endpoint)
        self.model = model
        self.key_provider = key_provider
        self.audit = []
        self.local_secret = secrets.token_urlsafe(24)
        self.server = None

    def __enter__(self):
        owner = self
        opener = urllib.request.build_opener(NoRedirect())

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                if (self.path != '/v1/chat/completions' or
                    self.headers.get('Authorization') != 'Bearer ' + owner.local_secret or
                    len(owner.audit) >= 12):
                    self.send_error(403)
                    return
                try:
                    length = int(self.headers.get('Content-Length', 0))
                    if not 0 < length < 2_000_000:
                        raise ValueError()
                    payload = json.loads(self.rfile.read(length))
                    if payload.get('model') != owner.model:
                        raise ValueError()
                except (ValueError, json.JSONDecodeError):
                    self.send_error(400)
                    return
                # Ask for usage when available; do not change model messages.
                if payload.get('stream'):
                    payload['stream_options'] = {'include_usage': True}
                body = json.dumps(payload).encode()
                record = {'request_bytes': len(body), 'model': owner.model,
                    'tools': [t.get('function', {}).get('name') for t in payload.get('tools', [])]}
                owner.audit.append(record)
                headers_sent = False
                try:
                    request = urllib.request.Request(owner.endpoint + '/chat/completions', data=body,
                        headers={'Authorization': 'Bearer ' + owner.key_provider().strip(),
                                 'Content-Type': 'application/json'})
                    with opener.open(request, timeout=60) as response:
                        record['http_status'] = response.status
                        self.send_response(response.status)
                        self.send_header('Content-Type', response.headers.get('Content-Type', 'text/event-stream'))
                        self.send_header('Connection', 'close')
                        self.end_headers()
                        headers_sent = True
                        pending = b''
                        while chunk := response.read1(65536):
                            self.wfile.write(chunk)
                            self.wfile.flush()
                            pending += chunk
                            while b'\n' in pending:
                                line, pending = pending.split(b'\n', 1)
                                if line.startswith(b'data: ') and line.strip() != b'data: [DONE]':
                                    try:
                                        event = json.loads(line[6:])
                                        if event.get('usage'):
                                            record['usage'] = event['usage']
                                    except (ValueError, UnicodeDecodeError):
                                        pass
                            if len(pending) > 1_000_000:
                                pending = b''
                except Exception as exc:
                    code = exc.code if isinstance(exc, urllib.error.HTTPError) else 502
                    record['http_status'] = code
                    record['error_type'] = type(exc).__name__
                    if not headers_sent:
                        try:
                            self.send_response(code)
                            self.send_header('Content-Type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({'error': {'message': f'Provider request failed (HTTP {code}). Check endpoint, credentials and model tool support.'}}).encode())
                        except OSError:
                            pass
                finally:
                    self.close_connection = True

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    @property
    def base_url(self):
        return f'http://127.0.0.1:{self.server.server_port}/v1'

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
