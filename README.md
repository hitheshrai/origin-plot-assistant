# Origin Plot Assistant

A Windows preview package for researchers: enter your API settings, select a CSV, describe your plot, and save an editable Origin project plus PNG/PDF figures.

**[Download the Windows package](dist/Origin-Plot-Assistant-0.1.0-Windows.zip)** · [User guide](PACKAGE_GUIDE.md) · [Extension guide](DEVELOPING.md)

## Use it

1. Have licensed Origin, 64-bit Python 3.11+ and OpenCode CLI installed. The tested combination is Origin 2024, Python 3.11.9 and OpenCode 1.18.27.
2. Download and extract the ZIP, then double-click **Start.cmd**. First launch installs the Python package into an isolated user environment.
3. Enter your API base URL, key and a model with tool calling. Test the connection and save.
4. Choose a CSV and describe a line, scatter or line-plus-scatter plot.

ASU default endpoint: `https://openai.rc.asu.edu/v1`. Each user supplies their own authorized Voyager/API access. Other OpenAI-compatible HTTPS endpoints are configurable but are not yet independently verified.

## Included

- Simple Windows window with persistent API settings and Windows-encrypted credential storage.
- Numeric CSV validation, multiple Y series, axis labels and linear/logarithmic axes.
- Dedicated Origin COM worker, export checks and saved-project verification.
- Reusable recipes: repeat a plot locally with **zero model calls**.
- A small MCP interface and separate backend modules for future features.

Numerical CSV values stay in the local plotting workflow. Your prompt, column names and tool results go to your configured provider. Sharing is disabled for package runs; local files/session records and provider policies still matter. See the user guide for the precise privacy boundary and limitations.

## Validation and status

The installed package completed a 1,001-row/two-series plot through OpenCode and ASU's `qwen3-coder-30b-a3b-instruct`: 39.127 seconds and 3,179 reported tokens. Recipe replay passed without API calls. These are single-run observations, not a percentage-savings benchmark.

This is version **0.1.0, a preview for a small research pilot**. It is a wheel plus Windows launcher, not a standalone executable bundling Python or Origin. Wider Origin-version, model and second-machine testing remain necessary. Known limits and troubleshooting are in [PACKAGE_GUIDE.md](PACKAGE_GUIDE.md).
