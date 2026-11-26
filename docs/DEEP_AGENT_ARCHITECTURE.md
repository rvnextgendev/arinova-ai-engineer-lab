# Optional Deep Agents learning module

Default: DEEP_AGENT_ENABLED=false. Set true in .env and recreate the API container after rebuilding. Select Deep Agent in /studio; standard skill remains the default selection. DEEP_AGENT_MODEL selects an Ollama model with reliable tool calling.

The adapter uses the actual deepagents SDK, per-request state backend, planning and SDK delegation. Its only custom business tool calls the existing registered skill executor with the original tenant and demo role. Manual skill selection restricts the allowed skill; automatic selection exposes the registered catalog. The response includes advisory answer, plan and skill call names. It is not verified output or an approval. No new write or approval tools are exposed. Six business tool calls and graph recursion limit 25 are learning safeguards, not a global cost or deadline guarantee.

GET /deep-agent/status; POST /deep-agent/{skill_id}/execute with the same Question body as standard skills. Disabled requests return 403. Existing routes are unchanged.

Run pytest tests/test_deep_agent.py and existing regression tests. Then exercise all four skills with a tool-capable local model. Dependency resolution, model compatibility, actual delegation and end-to-end behavior require local verification. This lab uses demo identities, not production authentication. Do not expose it publicly. Production work: authenticated tenant binding, sandbox review, durable approvals, streaming, budgets and comparative evaluation.
