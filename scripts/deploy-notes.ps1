# Controlli rapidi dopo deploy
$Backend = "https://puglia-profit-engine-api.onrender.com"
$Frontend = "https://TUO-PROGETTO.vercel.app"

Invoke-WebRequest "$Backend/health" | Select-Object StatusCode, Content
Invoke-WebRequest "$Backend/api/catalog" | Select-Object StatusCode, Content
Write-Host "Apri frontend: $Frontend"
