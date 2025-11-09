# MDC Career Path Advisor - Setup Script
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  MDC Career Path Advisor - Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[✓] Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "    $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "    [ERROR] Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "[✓] Checking Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "    Node.js $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "    [ERROR] Node.js not found. Please install Node.js 16+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[1/2] Setting up Backend..." -ForegroundColor Yellow
Set-Location backend

# Create virtual environment
if (Test-Path "venv") {
    Write-Host "    Virtual environment already exists, skipping creation" -ForegroundColor Gray
} else {
    Write-Host "    Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
}

# Activate and install
Write-Host "    Installing Python dependencies..." -ForegroundColor Gray
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt -q
Write-Host "    [✓] Backend setup complete!" -ForegroundColor Green

Write-Host ""
Write-Host "[2/2] Setting up Frontend..." -ForegroundColor Yellow
Set-Location ..

Write-Host "    Installing Node.js dependencies..." -ForegroundColor Gray
npm install --silent
Write-Host "    [✓] Frontend setup complete!" -ForegroundColor Green

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application:" -ForegroundColor White
Write-Host "1. Backend:  .\start-backend.ps1" -ForegroundColor Yellow
Write-Host "2. Frontend: .\start-frontend.ps1" -ForegroundColor Yellow
Write-Host "3. Open:     http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
