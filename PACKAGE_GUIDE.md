# Origin Plot Assistant 0.1.0

A Windows preview package for researchers who want to turn CSV files into editable Origin plots using OpenCode and their own OpenAI-compatible API. It also replays saved plotting recipes without an API call.

## Start

1. Install and license Origin. Origin 2024 is the initial test target.
2. Install Python 3.11 or newer, 64-bit, with Tkinter and pip. Python.org's standard Windows installer includes these.
3. Install OpenCode CLI and ensure `opencode --version` works. The tested version is 1.18.27. See https://opencode.ai/docs/ .
4. Extract the distribution ZIP into a normal local folder. Double-click **Start.cmd**. The first launch creates an isolated environment and downloads Python dependencies; later launches reuse it.
5. Enter your API base URL, API key and a tool-capable model ID. **Test API / load models**, then **Save settings**.
6. Browse to a CSV, describe the plot and click **Create plot**.

For ASU users, the base URL is `https://openai.rc.asu.edu/v1`. Obtain your own authorized key and exact model ID through Voyager. The feasibility study verified `qwen3-coder-30b-a3b-instruct`; available models and access may differ by account. Do not use another researcher's key.

An example request: “Plot Signal_A and Signal_B against Time_s as lines. Label X Time (s) and Y Signal (a.u.).” The included `example.csv` works with this request.

## Outputs and later sessions

Each request creates a new output subfolder containing a local CSV snapshot, PNG, PDF, editable `.opju` project, `recipe.json` and verification results. Successful AI runs also record provider-reported token usage. No existing project is overwritten.

Close and reopen the application using Start.cmd. API settings persist. The API key is encrypted with Windows DPAPI for your Windows account; it is not portable to another account/computer. Other programs running with your account's privileges may also be able to decrypt it. **Forget key** removes the application's stored credential.

To reuse a plot with the same or another compatible CSV, select the CSV and choose **Replay recipe (no API)**, then select a previous `recipe.json`. This repeats the plot locally using Origin and uses no inference tokens.

## Version 0.1 scope

- UTF-8 comma-separated CSV with a header, 2–64 uniquely named columns and 2–100,000 rows; maximum 20 MB.
- One numeric X column and 1–8 numeric Y columns. Text columns can exist but cannot be plotted.
- Line, scatter and line + scatter; linear or log10 axes; explicit axis labels.
- Selected values must be finite and nonempty. Log axes require positive values. No automatic sorting, imputation, normalization, fitting or smoothing.
- Labels/column names used in a plot cannot include quotes, backslashes, semicolons, dollar/percent signs, braces or control characters in this first version. Output folder names have corresponding script-syntax restrictions.
- The installed Origin graph template determines baseline appearance. Publication style presets and multi-panel figures are future additions.

## Data and credentials

Numerical values are processed locally. The model receives your plotting request, CSV column names, row counts and tool results. Headers and prompts can themselves contain sensitive information. The configured provider's data policies apply; ASU-hosted inference is remote, not offline.

The application uses a temporary loopback relay to add the real credential to HTTPS requests. OpenCode receives only a temporary local relay credential. The real API key is not placed in model messages, project files or the OpenCode configuration. Conversation sharing is disabled for these runs, only the selected provider is enabled, and the plotting agent receives only two narrow tools. Existing global OpenCode configuration is unchanged.

OpenCode can retain local session records, and each job retains a CSV copy and artifacts. Protect/delete those folders according to your research requirements. These settings are not an operating-system sandbox or a comprehensive privacy certification.

## Troubleshooting

- **Check setup** reports Python, OpenCode and Origin COM availability without launching Origin.
- API HTTP 401/403: verify the key and account access. A model-list request may be unavailable on some compatible providers; enter the ID manually.
- Model does not plot: choose a model with tool calling. Unsupported or ambiguous requests may need a more specific prompt.
- Origin fails or stalls: open Origin normally once to finish licensing/setup and dismiss dialogs, then retry. A timed-out automation worker can leave its dedicated Origin instance open. This preview reports the issue rather than closing unrelated Origin sessions.
- If using an OpenCode V2 release, its changed configuration schema may require an adapter update. This release targets the tested V1 CLI.

## Advanced use

```powershell
origin-plot doctor
origin-plot replay --csv data.csv --recipe recipe.json --output plots
origin-plot ask --csv data.csv --output plots --prompt "Plot Y against X"
```

Running `origin-plot` without arguments opens the Windows window. The source project documents extension points in `DEVELOPING.md`.

This is a preview for a small research pilot. A second-machine installation test and broader Origin/provider compatibility tests are still required before a general release.
