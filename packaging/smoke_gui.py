"""Construct the installed GUI without opening a visible user window."""
import json
import tkinter as tk
from origin_plot_assistant.ui import App

root = tk.Tk()
root.withdraw()
app = App(root)
root.update_idletasks()
buttons = [str(button.cget('text')) for button in app.buttons]
assert 'Create plot' in buttons
assert 'Replay recipe (no API)' in buttons
assert app.key.get() == ''
assert app.model_box.winfo_exists()
print(json.dumps({'gui_constructed': True, 'buttons': buttons,
                  'requested_size': [root.winfo_reqwidth(), root.winfo_reqheight()],
                  'key_field_initially_empty': True}))
root.destroy()
