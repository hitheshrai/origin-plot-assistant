from origin_plot_assistant.doctor import opencode_command, diagnose


def test_doctor_returns_registration_status_without_launching_origin():
    result = diagnose()
    assert isinstance(result['origin_com_registered'], bool)
    assert isinstance(result['ready'], bool)


def test_native_executable(monkeypatch):
    monkeypatch.setattr('shutil.which', lambda name: 'C:/tools/opencode.exe' if name == 'opencode.exe' else None)
    assert opencode_command() == ['C:/tools/opencode.exe']


def test_does_not_execute_unknown_batch_shim(monkeypatch):
    monkeypatch.setattr('shutil.which', lambda name: 'C:/missing/opencode.cmd' if name == 'opencode' else None)
    assert opencode_command() is None


def test_npm_shim_runs_with_node_without_shell(tmp_path, monkeypatch):
    script = tmp_path / 'node_modules/opencode-ai/bin/opencode'
    script.parent.mkdir(parents=True)
    script.write_text('// package entry point')
    mapping = {'opencode': str(tmp_path/'opencode.cmd'), 'node.exe': 'C:/node/node.exe'}
    monkeypatch.setattr('shutil.which', mapping.get)
    assert opencode_command() == ['C:/node/node.exe', str(script)]
