# Avvia backend FastAPI + frontend Vite in due finestre PowerShell.
# Esegui dalla root della cartella puglia-profit-engine.

$ErrorActionPreference = "Stop"

if (!(Test-Path ".\api\.env")) {
  Copy-Item ".\api\.env.example" ".\api\.env"
  Write-Host "Creato api/.env: modifica ADMIN_TOKEN, CORS_ORIGINS, WHATSAPP_PHONE quando vuoi." -ForegroundColor Yellow
}
if (!(Test-Path ".\web\.env")) {
  Copy-Item ".\web\.env.example" ".\web\.env"
  Write-Host "Creato web/.env: modifica VITE_API_BASE_URL quando deployi Render." -ForegroundColor Yellow
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\api'; py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\web'; npm install; npm run dev"

Write-Host "Backend: http://localhost:8000/health" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
