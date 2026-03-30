"""Shared helpers for printing Deep Agents + Leap0 run output.

Used by Deep Agent example scripts after ``agent.invoke(...)``.
"""

from __future__ import annotations

import itertools
import sys


def _tool_call_name_args(tc: object) -> tuple[str | None, dict[str, object]]:
    if isinstance(tc, dict):
        raw_args = tc.get("args")
        args = raw_args if isinstance(raw_args, dict) else {}
        return tc.get("name"), args
    args = getattr(tc, "args", None)
    return getattr(tc, "name", None), args if isinstance(args, dict) else {}


def collect_execute_commands(messages: list[object]) -> list[str]:
    """Return shell commands from ``execute`` tool calls in message order."""
    commands: list[str] = []
    for msg in messages:
        for tc in getattr(msg, "tool_calls", None) or []:
            name, args = _tool_call_name_args(tc)
            if name == "execute":
                commands.append(str(args.get("command", "")))
    return commands


def collect_execute_outputs(messages: list[object]) -> list[str]:
    """Return ``ToolMessage`` bodies for ``execute`` in message order."""
    return [
        str(getattr(msg, "content", ""))
        for msg in messages
        if getattr(msg, "name", None) == "execute"
    ]


def print_execute_summary(invoke_result: dict[str, object]) -> None:
    """Print each ``execute`` tool call and its sandbox output."""
    messages_obj = invoke_result.get("messages")
    if not isinstance(messages_obj, list):
        print("No messages in result.", file=sys.stderr)
        return

    commands = collect_execute_commands(messages_obj)
    outputs = collect_execute_outputs(messages_obj)

    print("\n--- execute tool (shell) ---")
    if not commands and not outputs:
        print("(no execute tool calls in this run)")
        return

    for i, (cmd, out) in enumerate(
        itertools.zip_longest(commands, outputs),
        start=1,
    ):
        cmd_s = cmd if cmd is not None else "(unknown)"
        out_s = out if out is not None else "(missing tool output in message list)"
        print(f"{i}. Command: {cmd_s}")
        print(f"   Returned:\n{out_s}")


def last_ai_text(messages: list[object]) -> str:
    """Plain text from the last ``AIMessage`` (handles OpenAI list-shaped content)."""
    for msg in reversed(messages):
        if type(msg).__name__ != "AIMessage":
            continue
        content = getattr(msg, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [
                str(block.get("text", ""))
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            return "\n".join(parts)
    return ""
