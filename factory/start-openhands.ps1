param([Parameter(Mandatory=$true)][string]$Project)
$ErrorActionPreference = "Stop"
if ($Project -cnotmatch '^[a-z][a-z0-9-]{0,63}$') { throw "Invalid project name" }
$root = Join-Path $PSScriptRoot "../generated"
$source = Join-Path $root $Project
if (!(Test-Path (Join-Path $source "manifest.json"))) { throw "Generate the project first" }
$workspace = Join-Path $PSScriptRoot "../agent-workspaces"
New-Item -ItemType Directory -Force -Path $workspace | Out-Null
$dest = Join-Path $workspace ($Project + "-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dest | Out-Null
# Copy only known starter files; never mount the source repository or secrets.
foreach ($name in @("app.py","business.py","arinova_core.py","runtime.py","web_app.py","test_app.py","manifest.json","README.md")) {
  $file = Join-Path $source $name
  if (Test-Path -LiteralPath $file -PathType Leaf) {
    if ((Get-Item -LiteralPath $file).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked file refused" }
    Copy-Item -LiteralPath $file -Destination $dest
  }
}
$dest = (Resolve-Path $dest).Path
Write-Host "Review workspace: $dest"
Write-Host "Agent Canvas: http://127.0.0.1:8780/canvas"
docker run --rm -it -p 127.0.0.1:8780:8000 -e AGENT_CANVAS_ALLOW_LAN_SESSION_KEY=true -v openhands-state:/home/openhands/.openhands --mount "type=bind,source=$dest,target=/projects" ghcr.io/openhands/agent-canvas:1.46.0
