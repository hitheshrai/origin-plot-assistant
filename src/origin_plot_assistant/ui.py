"""Small native Windows interface; plotting and network work stay off the UI thread."""
import json
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from . import __version__
from .api import list_models
from .data import inspect_csv
from .doctor import diagnose
from .jobs import create_job, run_worker
from .runner import run_assistant
from .settings import (app_dir, DEFAULT_ENDPOINT, DEFAULT_MODEL, forget_key,
                       load_key, load_settings, save_settings, validate_endpoint)


class App:
    def __init__(self, root):
        self.root = root
        root.title(f'Origin Plot Assistant {__version__}')
        root.geometry('850x840')
        root.minsize(740, 740)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.messages = queue.Queue()
        self.busy = False
        self.job = None
        self.buttons = []
        try:
            settings = load_settings()
        except (OSError, ValueError):
            settings = {'endpoint': DEFAULT_ENDPOINT, 'model': DEFAULT_MODEL}
        self.endpoint = tk.StringVar(value=settings['endpoint'])
        self.model = tk.StringVar(value=settings['model'])
        self.key = tk.StringVar()
        self.csv = tk.StringVar()
        self.output = tk.StringVar(value=str(app_dir() / 'plots'))
        self.status = tk.StringVar(value='Choose API settings and a CSV to begin.')
        self.columns = tk.StringVar(value='No CSV selected.')
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text='Origin Plot Assistant', font=('Segoe UI', 20, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w')
        ttk.Label(frame, text='Create editable Origin plots from CSV using your API and OpenCode.').grid(row=1, column=0, columnspan=3, sticky='w', pady=(0, 15))
        self.entry(frame, 2, 'API base URL', self.endpoint)
        self.entry(frame, 3, 'API key', self.key, show='•')
        ttk.Label(frame, text='Leave blank to keep the saved key. Stored encrypted for your Windows account.').grid(row=4, column=1, columnspan=2, sticky='w')
        ttk.Label(frame, text='Model ID').grid(row=5, column=0, sticky='w', pady=5)
        self.model_box = ttk.Combobox(frame, textvariable=self.model)
        self.model_box.grid(row=5, column=1, columnspan=2, sticky='ew', pady=5)
        actions = ttk.Frame(frame)
        actions.grid(row=6, column=1, columnspan=2, sticky='w', pady=(4, 14))
        self.button(actions, 'Test API / load models', self.test_api).pack(side='left', padx=(0, 7))
        self.button(actions, 'Save settings', self.save).pack(side='left', padx=(0, 7))
        self.button(actions, 'Forget key', self.forget).pack(side='left')
        ttk.Separator(frame).grid(row=7, column=0, columnspan=3, sticky='ew', pady=8)
        self.entry(frame, 8, 'CSV file', self.csv, span=1)
        self.button(frame, 'Browse…', self.browse_csv).grid(row=8, column=2, padx=(8, 0))
        ttk.Label(frame, textvariable=self.columns, wraplength=620).grid(row=9, column=1, columnspan=2, sticky='w')
        self.entry(frame, 10, 'Output folder', self.output, span=1)
        self.button(frame, 'Browse…', self.browse_output).grid(row=10, column=2, padx=(8, 0))
        ttk.Label(frame, text='Describe your plot').grid(row=11, column=0, sticky='nw', pady=(12, 0))
        self.prompt = tk.Text(frame, height=5, wrap='word', font=('Segoe UI', 10))
        self.prompt.grid(row=11, column=1, columnspan=2, sticky='nsew', pady=(12, 0))
        self.prompt.insert('1.0', 'Plot the numeric Y columns against the first numeric X column as a line graph. Use the column names for labels.')
        ttk.Label(frame, text='Supports line, scatter, line + scatter, multiple Y columns, axis labels and log scales.', wraplength=630).grid(row=12, column=1, columnspan=2, sticky='w', pady=5)
        row = ttk.Frame(frame)
        row.grid(row=13, column=1, columnspan=2, sticky='w', pady=8)
        self.button(row, 'Create plot', self.plot).pack(side='left', padx=(0, 7))
        self.button(row, 'Replay recipe (no API)', self.replay).pack(side='left', padx=(0, 7))
        self.button(row, 'Check setup', self.check_setup).pack(side='left')
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.grid(row=14, column=0, columnspan=3, sticky='ew', pady=5)
        ttk.Label(frame, textvariable=self.status, wraplength=770).grid(row=15, column=0, columnspan=3, sticky='w')
        self.details = tk.Text(frame, height=7, wrap='word', font=('Segoe UI', 10), state='disabled')
        self.details.grid(row=16, column=0, columnspan=3, sticky='nsew', pady=10)
        frame.rowconfigure(16, weight=1)
        links = ttk.Frame(frame)
        links.grid(row=17, column=0, columnspan=3, sticky='w')
        self.button(links, 'Open output folder', lambda: self.open_artifact('')).pack(side='left', padx=(0, 7))
        self.button(links, 'View PNG', lambda: self.open_artifact('figure.png')).pack(side='left', padx=(0, 7))
        self.button(links, 'Open Origin project', lambda: self.open_artifact('figure.opju')).pack(side='left')
        ttk.Label(frame, text='CSV values are processed locally. Your request, column names and tool results go to your API.\nOpenCode sharing is disabled for these runs. Local input copies and output files remain in each job folder.', wraplength=780).grid(row=18, column=0, columnspan=3, sticky='w', pady=(12, 0))
        root.after(100, self.poll)

    def button(self, parent, text, command):
        button = ttk.Button(parent, text=text, command=command)
        self.buttons.append(button)
        return button

    def entry(self, frame, row, title, variable, span=2, **kwargs):
        ttk.Label(frame, text=title).grid(row=row, column=0, sticky='w', padx=(0, 12), pady=5)
        ttk.Entry(frame, textvariable=variable, **kwargs).grid(row=row, column=1, columnspan=span, sticky='ew', pady=5)

    def show(self, text):
        self.details.configure(state='normal')
        self.details.delete('1.0', 'end')
        self.details.insert('1.0', text)
        self.details.configure(state='disabled')

    def background(self, action, done):
        if self.busy:
            return
        self.busy = True
        for button in self.buttons:
            button.configure(state='disabled')
        self.progress.start()
        def work():
            try:
                result = action()
                self.messages.put(('done', (done, result)))
            except Exception as exc:
                # Expected exceptions are curated; unknown errors never display request headers.
                text = str(exc) if isinstance(exc, (ValueError, RuntimeError, FileNotFoundError, UnicodeError)) else f'Operation failed ({type(exc).__name__}). Check setup and input format.'
                self.messages.put(('error', text))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == 'status':
                    self.status.set(value)
                elif kind == 'job':
                    self.job = Path(value)
                else:
                    self.busy = False
                    self.progress.stop()
                    for button in self.buttons:
                        button.configure(state='normal')
                    if kind == 'error':
                        self.status.set('Operation did not complete.')
                        self.show(value)
                    else:
                        callback, result = value
                        callback(result)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def save(self, quiet=False):
        try:
            previous = load_settings()
            if validate_endpoint(self.endpoint.get()) != previous['endpoint'] and not self.key.get().strip():
                raise ValueError('Enter the key for the new API endpoint before saving.')
            if not self.key.get().strip():
                load_key()
            save_settings(self.endpoint.get(), self.model.get(), self.key.get())
            self.key.set('')
            self.status.set('Settings saved. API key protected by Windows.')
            return True
        except Exception as exc:
            messagebox.showerror('Settings', str(exc) if isinstance(exc, ValueError) else 'Settings could not be saved.', parent=self.root)
            return False

    def forget(self):
        forget_key()
        self.key.set('')
        self.status.set('Saved API key removed.')

    def test_api(self):
        try:
            endpoint = validate_endpoint(self.endpoint.get())
            if endpoint != load_settings()['endpoint'] and not self.key.get().strip():
                raise ValueError('Enter a key for this new endpoint.')
            key = self.key.get().strip() or load_key()
        except ValueError as exc:
            messagebox.showerror('API settings', str(exc), parent=self.root)
            return
        self.status.set('Checking API connection…')
        def done(models):
            self.model_box['values'] = models
            self.status.set(f'API connected. {len(models)} models available. Select one with tool-calling support, then save.')
        self.background(lambda: list_models(endpoint, key), done)

    def browse_csv(self):
        selected = filedialog.askopenfilename(parent=self.root, filetypes=[('CSV', '*.csv')])
        if selected:
            self.csv.set(selected)
            self.status.set('Checking CSV…')
            def done(info):
                self.columns.set(f"{info['rows']:,} rows · Numeric columns: " + ', '.join(info['numeric_columns']))
                self.status.set('CSV is ready. Describe the plot you want.')
            self.background(lambda: inspect_csv(Path(selected)), done)

    def browse_output(self):
        selected = filedialog.askdirectory(parent=self.root)
        if selected:
            self.output.set(selected)

    def check_setup(self):
        self.show(json.dumps(diagnose(), indent=2))
        self.status.set('Setup checked. API access and Origin licensing are verified when used.')

    def plot(self):
        if not self.csv.get().strip():
            messagebox.showinfo('Select CSV', 'Choose a CSV file first.', parent=self.root)
            return
        if not self.save(quiet=True):
            return
        source, output = Path(self.csv.get()), Path(self.output.get())
        prompt = self.prompt.get('1.0', 'end').strip()
        settings = load_settings()
        self.status.set('Preparing plot…')
        def work():
            if not diagnose()['ready']:
                raise ValueError('Setup is incomplete. Use Check setup; Origin and OpenCode must be installed.')
            job = create_job(source, output)
            self.messages.put(('job', str(job)))
            self.messages.put(('status', 'Running OpenCode and Origin. This can take a minute…'))
            return run_assistant(job, prompt, settings, progress=lambda s: self.messages.put(('status', s)))
        self.background(work, self.finished)

    def replay(self):
        if not self.csv.get().strip():
            messagebox.showinfo('Select CSV', 'Choose the CSV to plot with the saved recipe.', parent=self.root)
            return
        selected = filedialog.askopenfilename(parent=self.root, title='Select a saved recipe', filetypes=[('Recipe JSON', '*.json')])
        if not selected:
            return
        source, output = Path(self.csv.get()), Path(self.output.get())
        self.status.set('Replaying recipe locally; no model request…')
        def work():
            recipe = json.loads(Path(selected).read_text(encoding='utf-8'))
            if recipe.get('schema_version') != 1:
                raise ValueError('Unsupported recipe version.')
            job = create_job(source, output)
            self.messages.put(('job', str(job)))
            return {'job': str(job), 'result': run_worker(job, recipe), 'summary': 'Recipe replay used no API calls.', 'usage': None}
        self.background(work, self.finished)

    def finished(self, outcome):
        self.job = Path(outcome['job'])
        result = outcome['result']
        if result.get('status') == 'passed':
            self.status.set('Plot created. PNG, PDF, editable Origin project and recipe saved.')
        else:
            self.status.set('Plot not completed. See details below.')
        usage = outcome.get('usage')
        tokens = (f"\nReported tokens: {usage['reported_tokens']:,}" if usage and usage['usage_available'] else '\nToken usage not reported by provider.' if usage else '\nModel tokens: 0')
        self.show((outcome.get('summary') or result.get('error') or json.dumps(result, indent=2)) + tokens + '\n\nOutputs: ' + str(self.job))

    def open_artifact(self, name):
        if self.job is None:
            messagebox.showinfo('No outputs yet', 'Create a plot first.', parent=self.root)
            return
        path = self.job / name if name else self.job
        if path.exists():
            os.startfile(path)
        else:
            messagebox.showinfo('File unavailable', 'This output was not created.', parent=self.root)

    def close(self):
        if self.busy:
            messagebox.showinfo('Operation in progress', 'Please wait for the current operation to finish before closing.', parent=self.root)
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    ttk.Style().theme_use('vista' if 'vista' in ttk.Style().theme_names() else 'clam')
    App(root)
    root.mainloop()
