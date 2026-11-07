# Start the NextStop Flask API on http://127.0.0.1:5000
Write-Host "Starting NextStop backend..." -ForegroundColor Cyan
Set-Location $PSScriptRoot\backend
foreach ($v in ".venv", "venv") {
    if (Test-Path "$v\Scripts\Activate.ps1") { . ".\$v\Scripts\Activate.ps1"; break }
}
if (-not (Test-Path ".env")) { Write-Host "No backend\.env found: running in offline mode (copy .env.example to .env to add keys)." -ForegroundColor Yellow }
python app.py
