# Extension points

`src/origin_plot_assistant/` separates the interface, model orchestration and plotting backend:

| Module | Responsibility |
|---|---|
| settings.py | API configuration and DPAPI credential storage |
| data.py | CSV parsing, validation and versioned recipe preparation |
| jobs.py / worker.py | Snapshot input, allocate unique outputs, isolate COM execution |
| backend.py | Typed recipe -> verified Origin graph/project/export |
| server.py | Small MCP tool contracts; no model-supplied file paths or raw LabTalk |
| api.py | Model discovery and credential-isolating HTTPS relay |
| runner.py | OpenCode configuration, model calls and token accounting |
| ui.py | Native Windows window, background jobs, saved settings and recipe replay |

To add a plot feature: define a typed recipe field, validate it before COM, implement it in the backend, expose only the needed MCP argument, add input/behavior tests, then verify the saved Origin project and exports. Bump the recipe schema for incompatible changes. Keep raw numerical arrays out of tool results by default.

Possible next additions: error bars, explicit style presets, graph titles, multi-panel layouts, additional table formats and a formal job cancellation/status API. Analysis operations such as normalization and fitting need explicit scientific semantics and provenance.

Development commands:

```powershell
python -m pytest
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
python packaging/build_zip.py
```

The ZIP includes the wheel, launchers, user guide and synthetic example; it excludes credentials, original research data, test sessions and internal experiment logs. The first-start script creates an isolated user environment. It is a source/wheel distribution with a launcher, not a standalone executable bundling Python or Origin.

Version 0.1 targets Windows and OpenCode 1.18.27. The optional authentication-only token-file CLI argument exists for controlled testing; normal users save a key through the masked GUI field. Neither the relay nor COM worker should log raw credentials.
