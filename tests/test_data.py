import json
from pathlib import Path
import pytest
from origin_plot_assistant.data import inspect_csv, prepare_plot, safe_label
from origin_plot_assistant.jobs import create_job, run_worker
from origin_plot_assistant.settings import validate_endpoint, save_settings, load_settings, save_key, load_key, forget_key


def table(tmp_path, text='Time,Signal,Group\n1,2,A\n2,4,B\n'):
    path = tmp_path / 'sample.csv'
    path.write_text(text, encoding='utf-8')
    return path


def test_metadata_contains_no_values(tmp_path):
    info = inspect_csv(table(tmp_path))
    assert info == {'columns': ['Time', 'Signal', 'Group'], 'numeric_columns': ['Time', 'Signal'],
                    'rows': 2, 'raw_values_returned': False}


@pytest.mark.parametrize('text', ['X,X\n1,2\n3,4', 'X,Y\n1\n2,3', 'X,Y\n1,2', ''])
def test_invalid_csv(tmp_path, text):
    with pytest.raises(ValueError):
        inspect_csv(table(tmp_path, text))


@pytest.mark.parametrize('value', ['', 'nan', 'inf', '-inf', 'not-a-number'])
def test_nonfinite_or_missing_selected_values(tmp_path, value):
    source = table(tmp_path, f'X,Y\n1,{value}\n2,3\n')
    with pytest.raises(ValueError):
        prepare_plot(source, {'x_column': 'X', 'y_columns': ['Y']})


def test_log_requires_positive_values(tmp_path):
    source = table(tmp_path, 'X,Y\n0,1\n2,3\n')
    with pytest.raises(ValueError, match='positive'):
        prepare_plot(source, {'x_column': 'X', 'y_columns': ['Y'], 'x_scale': 'log10'})


def test_preserves_order_and_values(tmp_path):
    source = table(tmp_path, 'X,Y\n2,8\n1,3\n')
    values, recipe = prepare_plot(source, {'x_column': 'X', 'y_columns': ['Y'], 'kind': 'scatter'})
    assert values == [[2.0, 8.0], [1.0, 3.0]]
    assert recipe['kind'] == 'scatter'
    assert recipe['schema_version'] == 1


@pytest.mark.parametrize('label', ['x";exit;', '$(system)', '%H', 'line\nexit', '\\b(label)', '{code}'])
def test_script_text_rejected(label):
    with pytest.raises(ValueError):
        safe_label(label)


def test_units_unicode_allowed():
    assert safe_label('Voltage (mV) / Impedance (Ω)')


def test_rejects_nonstring_label():
    with pytest.raises(ValueError):
        safe_label(None)


def test_snapshot_and_idempotency(tmp_path):
    source = table(tmp_path)
    job = create_job(source, tmp_path / 'outputs')
    original = (job / 'input.csv').read_bytes()
    source.write_text('changed')
    assert (job / 'input.csv').read_bytes() == original
    request = {'x_column': 'Time', 'y_columns': ['Signal']}
    _, cleaned = prepare_plot(job / 'input.csv', request)
    (job / 'request.json').write_text(json.dumps(cleaned))
    (job / 'result.json').write_text('{"status":"passed"}')
    assert run_worker(job, request)['status'] == 'passed'
    with pytest.raises(ValueError, match='different plot'):
        run_worker(job, {**request, 'kind': 'scatter'})


@pytest.mark.parametrize('endpoint', ['http://example.org/v1', 'https://user:secret@example.org/v1', 'https://example.org/v1?key=x', 'https://example.org/#fragment'])
def test_rejects_unsafe_endpoint(endpoint):
    with pytest.raises(ValueError):
        validate_endpoint(endpoint)


def test_settings_never_store_plaintext_key(tmp_path):
    dummy = 'synthetic-test-credential-not-real'
    save_settings('https://example.org/v1', 'test-model', dummy, tmp_path)
    assert load_key(tmp_path) == dummy
    assert dummy.encode() not in (tmp_path / 'credential.bin').read_bytes()
    assert dummy not in (tmp_path / 'settings.json').read_text()
    assert load_settings(tmp_path)['model'] == 'test-model'
    forget_key(tmp_path)
    assert not (tmp_path / 'credential.bin').exists()
