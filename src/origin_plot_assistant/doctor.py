import importlib.util
import platform
import shutil
import sys
from pathlib import Path


def opencode_command() -> list[str] | None:
    """Avoid passing a user prompt through a Windows batch-file shell."""
    native = shutil.which('opencode.exe')
    if native:
        return [native]
    found = shutil.which('opencode')
    if not found:
        return None
    if Path(found).suffix.lower() in ['.cmd', '.bat', '.ps1']:
        node = shutil.which('node.exe') or shutil.which('node')
        script = Path(found).parent / 'node_modules/opencode-ai/bin/opencode'
        return [node, str(script)] if node and script.is_file() else None
    return [found]


def diagnose() -> dict:
    result = {'windows': sys.platform == 'win32', 'python': platform.python_version(),
        'python_64bit': platform.architecture()[0] == '64bit',
        'opencode': bool(opencode_command()), 'origin_com_registered': False,
        'tkinter': importlib.util.find_spec('tkinter') is not None,
        'pywin32': importlib.util.find_spec('win32com') is not None}
    if result['windows'] and result['pywin32']:
        import ctypes
        lookup = ctypes.windll.ole32.CLSIDFromProgID
        lookup.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
        lookup.restype = ctypes.c_long
        result['origin_com_registered'] = lookup('Origin.Application', ctypes.create_string_buffer(16)) == 0
    result['ready'] = all(result[k] for k in ['windows', 'python_64bit', 'opencode', 'origin_com_registered', 'pywin32'])
    return result
