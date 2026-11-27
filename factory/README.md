# Software Factory pilot

This branch is based on the architect learning guide. The standalone studio is a configuration and architecture preview, not a live execution engine. Open `studio.html` locally in a browser. Select capabilities and export the project manifest. No model calls, deployment, security checks or code generation are performed by the preview.

Next integration: extract tested core SDK interfaces; bind capability registry to actual implementations; generate runnable projects with templates; add business plugin contracts; run tests and security gates in CI; expose real workflow events through an authenticated API. Keep factory disabled by default in the existing application until integration tests pass.
