"""Nonsecret settings and Windows user-bound DPAPI credential storage."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_ENDPOINT = 'https://openai.rc.asu.edu/v1'
DEFAULT_MODEL = 'qwen3-coder-30b-a3b-instruct'


def app_dir() -> Path:
    return Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'OriginPlotAssistant'


def validate_endpoint(value: str) -> str:
    value = value.strip().rstrip('/')
    url = urlsplit(value)
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError('Use an HTTPS API base URL without credentials, query or fragment, such as https://openai.rc.asu.edu/v1.')
    return value


def load_settings(root: Path | None = None) -> dict:
    root = root or app_dir()
    defaults = {'endpoint': DEFAULT_ENDPOINT, 'model': DEFAULT_MODEL}
    path = root / 'settings.json'
    if path.exists():
        defaults.update(json.loads(path.read_text(encoding='utf-8')))
    return defaults


def save_settings(endpoint: str, model: str, key: str = '', root: Path | None = None):
    root = root or app_dir()
    endpoint = validate_endpoint(endpoint)
    if not model.strip() or len(model) > 200 or any(ord(c) < 32 for c in model):
        raise ValueError('Enter a valid model ID from your provider.')
    root.mkdir(parents=True, exist_ok=True)
    if key:
        save_key(key, root)
    path = root / 'settings.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'endpoint': endpoint, 'model': model.strip()}, indent=2), encoding='utf-8')
    temporary.replace(path)


def save_key(key: str, root: Path | None = None):
    import win32crypt
    root = root or app_dir()
    key = key.strip()
    if not key or any(c in key for c in '\r\n'):
        raise ValueError('Enter a nonempty API key on one line.')
    encrypted = win32crypt.CryptProtectData(key.encode('utf-8'), 'Origin Plot Assistant', None, None, None, 0)
    root.mkdir(parents=True, exist_ok=True)
    temporary = root / 'credential.tmp'
    temporary.write_bytes(encrypted)
    temporary.replace(root / 'credential.bin')


def load_key(root: Path | None = None) -> str:
    import win32crypt
    root = root or app_dir()
    path = root / 'credential.bin'
    if not path.exists():
        raise ValueError('Save an API key in Settings first.')
    try:
        return win32crypt.CryptUnprotectData(path.read_bytes(), None, None, None, 0)[1].decode('utf-8')
    except Exception:
        raise ValueError('The saved key cannot be unlocked by this Windows account. Enter it again.') from None


def forget_key(root: Path | None = None):
    (root or app_dir()).joinpath('credential.bin').unlink(missing_ok=True)
