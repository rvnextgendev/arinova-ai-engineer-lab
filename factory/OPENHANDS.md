# OpenHands operating guide

Local opt-in pilot. No automatic agent API, approval enforcement or merge.

## 1. Prerequisites

Run docker info and ollama list in PowerShell. Docker Desktop must be running.

## 2. Generate project

Use Software Factory above. Enter the exact generated project name below.

## 3. Define requirements

Describe functionality, acceptance criteria and constraints.

## 4. Prepare isolated workspace

Run the prepared PowerShell command from the repository root. Keep the terminal open.

## 5. Configure model

In Agent Canvas choose an Ollama-compatible provider, model llama3.2:latest and host http://host.docker.internal:11434 (append /v1 for OpenAI-compatible configuration).

## 6. Execute coding task

Open Agent Canvas, select the mounted /projects workspace and paste the prepared task. Review any permission requests.

## 7. Inspect changes

Review files in the agent-workspaces directory printed by the launcher. Do not copy secrets into it.

## 8. Run tests

From the reviewed workspace run python -m unittest -v after inspecting the generated code. Prefer an isolated test environment.

## 9. Human approval

Review code, test output and security implications. Record approval only after inspection.

## 10. Integrate changes

Manually copy approved changes into the customer project and use Git diff before committing. No automatic merge.

## 11. Shutdown

Stop the Docker launcher with Ctrl+C. Review workspace files remain on disk.

## Commands

```powershell
docker info
ollama list
python factory/preview_server.py
# In another terminal, from repository root:
.\factory\start-openhands.ps1 -Project "motor-ai-studio-v5"
```

Factory: http://127.0.0.1:8766/#openhands

Canvas: http://127.0.0.1:8780/canvas

## Troubleshooting

If Docker image pull fails, verify the configured image/tag against official OpenHands documentation. If model connection fails, verify host Ollama is reachable from Docker; do not expose Ollama to untrusted networks. If the model cannot use tools reliably, choose a supported coding model. If port 8780 is occupied, stop the conflicting service after identifying it. Never run unreviewed agent code on the host. The launcher and model compatibility require local verification.
