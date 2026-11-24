$ErrorActionPreference = "Stop"
docker compose up -d
if ($LASTEXITCODE -ne 0) { throw "Startup failed" }
Write-Host "UI: http://localhost:8501 | API: http://localhost:8000/docs"
