param([string]$Repo = "$HOME\source\arinova-ai-engineer-lab", [string]$Project = ('motor-openhands-' + (Get-Date -Format 'yyyyMMdd-HHmmss')))
$ErrorActionPreference = 'Stop'
function Check-Native { if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE)" } }
if ($Project -cnotmatch '^[a-z][a-z0-9-]{0,63}$') { throw 'Invalid project name' }
foreach ($cmd in @('git','python','docker','ollama')) { if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "Install $cmd first" } }
if (!(Test-Path $Repo)) { git clone --branch feature/ai-software-factory https://github.com/rvnextgendev/arinova-ai-engineer-lab.git $Repo; Check-Native }
Set-Location $Repo
if (git status --porcelain --untracked-files=no) { throw 'Commit or stash tracked local changes before setup.' }
git fetch origin; Check-Native
git switch feature/ai-software-factory; Check-Native
git pull --ff-only origin feature/ai-software-factory; Check-Native
foreach ($f in @('generate.py','preview_server.py','start-openhands.ps1')) { if (!(Test-Path "factory/$f")) { throw "Missing factory/$f" } }
docker info | Out-Null; Check-Native
try { $models = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' } catch { Start-Process ollama -ArgumentList 'serve'; Start-Sleep 5; $models = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' }
if ($models.models.name -notcontains 'llama3.2:latest') { ollama pull llama3.2; Check-Native }
foreach ($port in @(8766,8770,8780)) { if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "Port $port already in use. Stop the existing service and rerun." } }
$manifest = @{project=$Project;business_plugin='motor_dtc_processor';model='ollama';capabilities=@{rag=$true;hybrid_search=$true;langgraph=$true;mcp=$true;skills=$true;evaluation=$true;guardrails=$true;human_approval=$true;observability=$true;ci_cd=$true}}
$config = Join-Path ([IO.Path]::GetTempPath()) ("arinova-" + [guid]::NewGuid() + '.json')
try { $manifest | ConvertTo-Json -Depth 5 | Set-Content -Encoding ascii $config; python factory/generate.py $config --output generated; Check-Native } finally { Remove-Item $config -ErrorAction SilentlyContinue }
$dest = Join-Path $Repo "generated/$Project"
if (!(Test-Path "$dest/manifest.json")) { throw 'Generation failed: manifest missing' }
Push-Location $dest
try { python -m unittest -v; Check-Native } finally { Pop-Location }
$python = (Get-Command python).Source
Start-Process -FilePath $python -ArgumentList 'factory/preview_server.py --no-browser' -WorkingDirectory $Repo
Start-Process -FilePath $python -ArgumentList 'web_app.py' -WorkingDirectory $dest
Write-Host "Project: $dest"
Write-Host 'Factory: http://127.0.0.1:8766/#openhands'
Write-Host 'Customer: http://127.0.0.1:8770'
Write-Host 'OpenHands: http://127.0.0.1:8780/canvas (after Docker starts)'
Write-Host 'Ollama from Docker: http://host.docker.internal:11434'
Write-Host 'Configure model and submit coding task manually in Canvas.'
Start-Process 'http://127.0.0.1:8766/#openhands'
& .\factory\start-openhands.ps1 -Project $Project
Check-Native
