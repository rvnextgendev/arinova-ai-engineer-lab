# Central Software Factory
Install factory/requirements-studio.txt, then run python factory/policy_studio.py and open http://127.0.0.1:8790/factory.
Register a unique project ID, customer and requirements. Select capabilities, save configuration, create architecture plan, generate starter. Refresh to verify persistence.
Run python -m unittest discover -s factory -p test_central_projects.py -v.
State is local SQLite under factory-state/projects.sqlite3; generated artifacts under generated/. Do not commit customer state or documents. Use fictional inputs.
Core inventory version 0.1.0 resolves dependencies and records source availability. Generated project is the existing generic DTC fixture starter with requirements and architecture plan. Selected adapters are not automatically wired. Policy Studio and Architect Labs remain separate existing modules. No production authentication, PostgreSQL registry, independent SDK packaging, automatic OpenHands orchestration, quality gates or remote delivery is added. Runtime validation remains necessary.
