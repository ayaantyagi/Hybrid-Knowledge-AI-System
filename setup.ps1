# PowerShell setup script for Blue Enigma project
# Run: .\setup.ps1

param(
    [switch]$RunTests
)

Write-Host "Creating virtual environment .venv..."
python -m venv .venv

Write-Host "Activating virtual environment..."
# This will affect only the current PowerShell session
.\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip and installing requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt

if ($RunTests) {
    Write-Host "Running pytest..."
    python -m pytest -q
}

Write-Host "Setup complete. Activate the venv with: .\.venv\Scripts\Activate.ps1"