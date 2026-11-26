# Studio demo reliability checks

Changes: ten-minute browser request timeout (does not cancel server execution), visible busy feedback, required question/tenant validation, automatic routing highlight reset, distinct availability errors, and comparison results that retain both engine outcomes and report partial failures.

Validation: source review and static contract checks only; browser and live Docker/Ollama/PostgreSQL execution have not been run.

Local acceptance: run pytest tests/test_studio_contract.py and the existing test suite. Open /studio and verify health, PDF upload (valid/invalid/duplicate), all four skills, unknown routing, empty input, retrieval, deep disabled/enabled, compare success/one failure/both failures, judge, security, telemetry, circuit status, workflow approval/cancel/replay, MCP discovery, and module console. Use synthetic data and a disposable database for failure and workflow tests. Verify network failure and timeout feedback. Do not treat static checks as end-to-end validation.
