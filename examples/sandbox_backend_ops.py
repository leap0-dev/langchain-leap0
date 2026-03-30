"""Exercise ``Leap0Sandbox`` the same way LangChain ``SandboxIntegrationTests`` does.

Covers:

- ``execute`` — shell output and exit code
- ``write`` / ``read`` / ``edit`` — inherited from ``BaseSandbox`` (shell-backed)
- ``upload_files`` / ``download_files`` — Leap0 filesystem API (bytes roundtrip)
- ``download_files`` with a relative path — ``error="invalid_path"`` (no API call)

Requires ``LEAP0_API_KEY``. Run from the repository root::

    uv run python examples/sandbox_backend_ops.py
"""

from __future__ import annotations

import os
import sys

from leap0.client import Leap0Client

from langchain_leap0 import Leap0Sandbox

_TEST_ROOT = "/tmp/test_sandbox_ops"  # noqa: S108


def _banner(title: str) -> None:
    print(f"\n--- {title} ---")


def _demo_execute(backend: Leap0Sandbox) -> None:
    _banner("execute")
    result = backend.execute("echo 'Leap0 execute() ok'")
    print(result.output.strip())
    print("exit_code:", result.exit_code)


def _demo_write_read(backend: Leap0Sandbox) -> None:
    _banner("write + read (BaseSandbox over execute)")
    path = f"{_TEST_ROOT}/new_file.txt"
    content = "Hello, sandbox!\nLine 2\nLine 3"
    write_result = backend.write(path, content)
    print("write error:", write_result.error)
    cat = backend.execute(f"cat {path}")
    print("cat matches write:", cat.output.strip() == content)
    body = backend.read(path)
    print("read() contains Line 2:", "Line 2" in body)


def _demo_edit(backend: Leap0Sandbox) -> None:
    _banner("edit (BaseSandbox)")
    path = f"{_TEST_ROOT}/edit_single.txt"
    backend.write(path, "Hello world\nGoodbye world\nHello again")
    edit_result = backend.edit(path, "Goodbye", "Farewell")
    print("edit occurrences:", edit_result.occurrences, "error:", edit_result.error)
    print("Farewell in file:", "Farewell world" in backend.read(path))


def _demo_upload_download_roundtrip(backend: Leap0Sandbox) -> None:
    _banner("upload_files + download_files (binary roundtrip)")
    test_path = "/tmp/leap0_roundtrip.bin"  # noqa: S108
    test_content = b"Roundtrip: special \n\t\r\x00"
    up = backend.upload_files([(test_path, test_content)])
    print("upload errors:", [r.error for r in up])
    down = backend.download_files([test_path])
    print("download error:", down[0].error)
    print("bytes match:", down[0].content == test_content)


def _demo_download_invalid_path(backend: Leap0Sandbox) -> None:
    _banner("download_files relative path -> invalid_path")
    responses = backend.download_files(["relative/path.txt"])
    print("path:", responses[0].path, "error:", responses[0].error)


def main() -> int:
    """Run sandbox backend demos; tear down the Leap0 sandbox when done."""
    if not os.environ.get("LEAP0_API_KEY"):
        print("Set LEAP0_API_KEY in your environment.", file=sys.stderr)
        return 1

    client = Leap0Client()
    sandbox = client.sandboxes.create()
    backend = Leap0Sandbox(client=client, sandbox=sandbox)
    try:
        prep = backend.execute(f"rm -rf {_TEST_ROOT} && mkdir -p {_TEST_ROOT}")
        if prep.exit_code != 0:
            print("Failed to prepare test dir:", prep.output, file=sys.stderr)
            return 1

        _demo_execute(backend)
        _demo_write_read(backend)
        _demo_edit(backend)
        _demo_upload_download_roundtrip(backend)
        _demo_download_invalid_path(backend)
    finally:
        client.sandboxes.delete(sandbox)
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
