Set-Location $PSScriptRoot
& ".venv\Scripts\Activate.ps1"
pytest @args
