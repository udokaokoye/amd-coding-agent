# Setup script for Local Coding Agent
# Run in PowerShell: .\setup.ps1

Write-Host ""
Write-Host "LEO CODE SETUP" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

# Check for Python
Write-Host "Checking Python..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python not found. Please install Python 3.10+ first." -ForegroundColor Red
    exit 1
}
Write-Host "OK: Python found at $($python.Source)" -ForegroundColor Green

# Check for Foundry Local
Write-Host ""
Write-Host "Checking Foundry Local CLI..." -ForegroundColor Yellow
$foundry = Get-Command foundry -ErrorAction SilentlyContinue
if (-not $foundry) {
    Write-Host "Installing Foundry Local via winget..." -ForegroundColor Yellow
    winget install Microsoft.FoundryLocal
    Write-Host ""
    Write-Host "Please restart your terminal and run this script again." -ForegroundColor Yellow
    exit 0
}
Write-Host "OK: Foundry Local found" -ForegroundColor Green

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
}
Write-Host "OK: Virtual environment ready" -ForegroundColor Green

# Activate and install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
pip install foundry-local-sdk-winml --quiet
Write-Host "OK: Dependencies installed" -ForegroundColor Green

# Pre-download the model
Write-Host ""
Write-Host "Pre-downloading model (phi-3.5-mini)..." -ForegroundColor Yellow
foundry model download phi-3.5-mini
Write-Host "OK: Model ready" -ForegroundColor Green

Write-Host ""
Write-Host "========================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the demo:" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "  python demo.py sample_project" -ForegroundColor Yellow
Write-Host ""
