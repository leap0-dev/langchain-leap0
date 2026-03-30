r"""Deep agent using Leap0 for a multi-step file + shell task.

Demonstrates ``create_deep_agent(..., backend=Leap0Sandbox(...))`` when the model
must combine file tools and ``execute`` (same surface area as integration tests
that mix writes, reads, and shell).

The user task asks for a **POSIX text file** (every line ends with a newline,
including the last) so ``wc -l`` reports **2** for two lines: ``wc -l`` counts
newline characters, not informal "rows" without a final newline.

Environment:

- ``LEAP0_API_KEY`` — Leap0 API key (https://leap0.dev).
- ``OPENAI_API_KEY`` — OpenAI API key.
- ``OPENAI_MODEL`` — optional, default ``openai:gpt-4o``.

Run from the repository root::

    uv run python examples/deep_agent_workspace.py
"""

from __future__ import annotations

import os
import sys

from deepagents import create_deep_agent
from leap0.client import Leap0Client
from sandbox_run_output import last_ai_text, print_execute_summary

from langchain_leap0 import Leap0Sandbox

_DEFAULT_OPENAI_MODEL = "openai:gpt-4o"
_WORKSPACE_ROOT = "/tmp/test_sandbox_ops"  # noqa: S108


def main() -> int:
    """Run a multi-step agent task; print shell steps and the final model reply."""
    if not os.environ.get("LEAP0_API_KEY"):
        print("Set LEAP0_API_KEY in your environment.", file=sys.stderr)
        return 1
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY in your environment.", file=sys.stderr)
        return 1

    model = os.environ.get("OPENAI_MODEL", _DEFAULT_OPENAI_MODEL).strip()

    client = Leap0Client()
    sandbox = client.sandboxes.create()
    backend = Leap0Sandbox(client=client, sandbox=sandbox)
    try:
        prep = backend.execute(
            f"rm -rf {_WORKSPACE_ROOT} && mkdir -p {_WORKSPACE_ROOT}",
        )
        if prep.exit_code != 0:
            print("Failed to prepare workspace dir:", prep.output, file=sys.stderr)
            return 1

        agent = create_deep_agent(
            model=model,
            system_prompt=(
                "You are a coding assistant with sandbox access. "
                f"Prefer absolute paths under {_WORKSPACE_ROOT} for project files."
            ),
            backend=backend,
        )
        # wc -l counts newline bytes; two POSIX lines => first field of wc -l is 2.
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Under {_WORKSPACE_ROOT}, create notes.txt as a POSIX "
                            "text file with exactly two lines of content. Every line "
                            "must end with a newline character, including the final "
                            "line. Then run `wc -l "
                            f"{_WORKSPACE_ROOT}/notes.txt` and state in your final "
                            "answer that the first number in the output is 2."
                        ),
                    },
                ],
            },
        )
        if isinstance(result, dict):
            print_execute_summary(result)
            msgs = result.get("messages")
            if isinstance(msgs, list):
                print("\n--- final model message ---")
                print(last_ai_text(msgs) or "(no AI text extracted)")
        else:
            print(result)
    finally:
        client.sandboxes.delete(sandbox)
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
