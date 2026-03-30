# Examples

Run from the package root (`langchain-leap0/`).

These mirror what LangChain’s **`SandboxIntegrationTests`** exercises for partner sandboxes (see `langchain_tests.integration_tests.sandboxes`): shell execution, `BaseSandbox` text operations (`write` / `read` / `edit` via `execute`), binary `upload_files` / `download_files`, and path validation.

| Script | Purpose |
|--------|---------|
| `basic_sandbox.py` | Minimal: `Leap0Client` → `sandboxes.create()` → `Leap0Sandbox.execute()`; teardown `delete` + `close`. |
| `sandbox_backend_ops.py` | Integration-style tour: `execute`, `write`/`read`/`edit`, upload/download roundtrip (bytes + null), relative-path download → `invalid_path`. |
| `deep_agent_sandbox.py` | `create_deep_agent(..., backend=Leap0Sandbox(...))` — single-turn “create script and run it”; prints a short **execute** summary (not the full message graph). |
| `deep_agent_workspace.py` | Same agent setup; POSIX two-line `notes.txt` (trailing `\n` on each line) + `wc -l` should read `2`; prints execute summary and final model reply. |
| `sandbox_run_output.py` | Helpers used by the Deep Agent examples (not run standalone). |

## Environment

**`basic_sandbox.py`**, **`sandbox_backend_ops.py`**

- `LEAP0_API_KEY`

**`deep_agent_sandbox.py`**, **`deep_agent_workspace.py`**

- `LEAP0_API_KEY`
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (optional, default `openai:gpt-4o`)

## Commands

```bash
uv run python examples/basic_sandbox.py
uv run python examples/sandbox_backend_ops.py
uv run python examples/deep_agent_sandbox.py
uv run python examples/deep_agent_workspace.py
```

Deep Agents sandbox backends: https://docs.langchain.com/oss/python/deepagents/sandboxes
