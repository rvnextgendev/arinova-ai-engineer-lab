# Software Factory v0.1 pilot

Opt-in local project generation; existing lab unchanged. Python 3.11+, no additional dependencies for generator.

1. Open `factory/studio.html` in a browser, enable preview, select capabilities and export JSON.
2. From repository root run `python factory/generate.py factory/example.json --output generated` (or use exported JSON).
3. Run `cd generated/motor-dtc-assistant` then `python app.py` and `python -m unittest`.
4. Replace `business.py` with customer logic. Generated project includes manifest, CLI, unit tests and optional GitHub Actions test workflow.

Factory tests from repository root: `python -m unittest factory.test_generate`.

The registry validates feature names, types and selected dependencies. It does NOT connect selected AI features to runtime adapters. The pilot echoes input via a business plugin; no RAG, agents, model calls, production security or deployment are executed. UI remains a standalone manifest preview. CI template runs tests only. Next: extract core SDK from learning reference, wire actual adapters and workflow events, add authenticated API/UI integration and security/deployment gates. Tests supplied but execution not verified in this commit.
