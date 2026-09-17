# Version 0.1.0 validation

Date: 2026-09-17. This is a small research-pilot preview, verified on one Windows machine.

## Passed checks

- 30 automated tests: CSV validation, missing/nonfinite values, log-scale requirements, data order preservation, script-text rejection, immutable input snapshots, idempotency, safe endpoint handling, Windows credential encryption/deletion, shell-free OpenCode launch resolution and the Origin setup check.
- Wheel built and installed in a separate environment.
- A clean environment with no inherited packages installed the wheel and all dependencies successfully. `packaging/constraints.txt` records the runtime versions for the ZIP launcher, including pywin32 312 and MCP 1.30.0.
- The clean installation discovered both MCP tools, inspected a CSV and created a verified Origin plot through the installed package. The COM worker took 25.174 seconds; no model calls were made for this transport test.
- Native window construction tested while hidden; API-key field initially empty and all main controls present.
- PowerShell launcher parsed without syntax errors.
- Installed-package live test through OpenCode 1.18.27 and ASU `qwen3-coder-30b-a3b-instruct`: 1,001 rows, two Y series, explicit axis labels, PNG/PDF/OPJU and saved recipe. 39.127 seconds, 3 provider requests, 3,179 reported tokens.
- Saved-recipe replay: same two-series plot, 26.961 seconds, zero model calls.
- Single-series scatter: four synthetic rows, 23.981 seconds, zero model calls.
- Two-series line-plus-scatter with logarithmic axes: four synthetic rows, 25.325 seconds, zero model calls. Export visually inspected.
- Data were read back exactly from Origin. Expected curve counts and export files were checked. Saved projects reopened with the original numerical data and graph.

The first packaged live test used existing pywin32 311/MCP 1.27.2; the clean-install transport test also verified pywin32 312/MCP 1.30.0. The final setup-check fix uses the Windows COM API directly instead of assuming a pywin32 helper exists.

## Interpretation and limits

The measurements demonstrate a functioning package and repeatable local plotting. They are not a throughput benchmark, a percentage token-savings claim or a researcher usability study. Real prompts and retries can consume more tokens; provider usage may be absent on other endpoints.

The real test API credential was loaded only for authentication, not printed or copied into the repository. Numeric CSV rows were handled locally; tool results exposed column metadata and verification outcomes. This is not a system-wide traffic audit or proof of a provider's retention policy.

Still needed before broad release: second-machine installation, additional Origin versions/providers, larger/messier datasets, publication styles and stronger cancellation/modal-dialog recovery. The launcher requires Python, OpenCode and a licensed Origin installation. It does not bundle those products.

All inputs used for these checks were synthetic. Local experiment logs and user-specific paths are intentionally excluded from GitHub and the distribution ZIP.
