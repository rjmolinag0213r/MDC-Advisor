# Start Backend Server
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Starting Backend Server..." -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Set-Location backend
.\venv\Scripts\Activate.ps1
python app.py
