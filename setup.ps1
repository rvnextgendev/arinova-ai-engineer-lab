$ErrorActionPreference = "Stop"
docker compose version
if ($LASTEXITCODE -ne 0) { throw "Start Docker Desktop first" }
if (!(Test-Path .env)) { Copy-Item .env.example .env }
ollama pull llama3.2
if ($LASTEXITCODE -ne 0) { throw "Install and start Ollama first" }
docker compose build
if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
