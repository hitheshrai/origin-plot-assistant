$ErrorActionPreference = 'Stop'
try {
    $packageRoot = $PSScriptRoot
    $appRoot = Join-Path $env:LOCALAPPDATA 'OriginPlotAssistant'
    $runtimeRoot = Join-Path $appRoot 'venv'
    $pythonPath = Join-Path $runtimeRoot 'Scripts/python.exe'
    $wheel = Get-ChildItem -LiteralPath $packageRoot -Filter 'origin_plot_assistant-*.whl' | Sort-Object Name | Select-Object -Last 1
    if (-not $wheel) { throw 'The package wheel is missing. Extract the complete ZIP first.' }
    $constraints = Join-Path $packageRoot 'constraints.txt'
    if (-not (Test-Path -LiteralPath $constraints)) { throw 'Dependency constraints are missing. Extract the complete ZIP first.' }
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $pythonCommand) { throw 'Install Python 3.11 or newer (64-bit) from python.org, then run Start.cmd again.' }
        & $pythonCommand.Source -c "import sys,struct; assert sys.version_info >= (3,11) and struct.calcsize('P') == 8, 'Python 3.11+ 64-bit is required'"
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ 64-bit is required.' }
        New-Item -ItemType Directory -Force -Path $appRoot | Out-Null
        & $pythonCommand.Source -m venv $runtimeRoot
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the isolated Python environment.' }
    }
    $installedMarker = Join-Path $appRoot 'installed-wheel.txt'
    $fingerprint = (Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256).Hash + ':' + (Get-FileHash -LiteralPath $constraints -Algorithm SHA256).Hash
    $installed = if (Test-Path -LiteralPath $installedMarker) { (Get-Content -LiteralPath $installedMarker -Raw).Trim() } else { '' }
    if ($installed -ne $fingerprint) {
        Write-Host 'Installing Origin Plot Assistant and its Python dependencies…'
        & $pythonPath -m pip install --upgrade --force-reinstall --constraint $constraints $wheel.FullName
        if ($LASTEXITCODE -ne 0) { throw 'Installation failed. Check network access and the pip error above.' }
        Set-Content -LiteralPath $installedMarker -Value $fingerprint
    }
    if (-not (Get-Command opencode -ErrorAction SilentlyContinue)) {
        Write-Host 'OpenCode CLI is not on PATH. Install it from https://opencode.ai/docs/ and restart this launcher.'
    }
    $windowPython = Join-Path $runtimeRoot 'Scripts/pythonw.exe'
    Start-Process -FilePath $windowPython -ArgumentList '-m','origin_plot_assistant' -WindowStyle Hidden
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
