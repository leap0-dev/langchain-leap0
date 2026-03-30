"""Leap0 sandbox backend implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileOperationError,
    FileUploadResponse,
)
from deepagents.backends.sandbox import BaseSandbox
from leap0 import Leap0APIError, Leap0Error
from leap0.models import SandboxRef, sandbox_id_of

if TYPE_CHECKING:
    from leap0.client import Leap0Client

_HTTP_NOT_FOUND = 404
_HTTP_FORBIDDEN = 403


class Leap0Sandbox(BaseSandbox):
    """Leap0 sandbox implementation conforming to SandboxBackendProtocol."""

    def __init__(
        self,
        *,
        client: Leap0Client,
        sandbox: SandboxRef,
        timeout: int = 30 * 60,
    ) -> None:
        """Create a backend connected to an existing Leap0 sandbox.

        Args:
            client: Authenticated Leap0 API client.
            sandbox: Sandbox id string or ``Sandbox`` / ``SandboxStatus`` model.
            timeout: Default command timeout in seconds when ``execute()`` is
                called without an explicit ``timeout``.
        """
        self._client = client
        self._sandbox = sandbox
        self._sandbox_id = sandbox_id_of(sandbox)
        self._default_timeout = timeout

    @property
    def id(self) -> str:
        """Return the Leap0 sandbox id."""
        return self._sandbox_id

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Execute a shell command inside the sandbox.

        Args:
            command: Shell command string to execute.
            timeout: Maximum time in seconds to wait for this command.

                If None, uses the backend's default timeout.

        Returns:
            ExecuteResponse containing output, exit code, and truncation flag.
        """
        effective_timeout = timeout if timeout is not None else self._default_timeout
        result = self._client.process.execute(
            self._sandbox,
            command=command,
            timeout=effective_timeout,
        )
        return ExecuteResponse(
            output=result.result,
            exit_code=result.exit_code,
            truncated=False,
        )

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download files from the sandbox.

        Non-absolute paths return ``invalid_path`` without calling the API.
        Failures are reported per path via ``FileDownloadResponse.error``.
        """
        responses: list[FileDownloadResponse] = []
        for path in paths:
            if not path.startswith("/"):
                responses.append(
                    FileDownloadResponse(path=path, content=None, error="invalid_path"),
                )
                continue
            try:
                content = self._client.filesystem.read_file_bytes(
                    self._sandbox,
                    path=path,
                )
            except Leap0APIError as exc:
                responses.append(
                    FileDownloadResponse(
                        path=path,
                        content=None,
                        error=self._map_filesystem_api_error(exc),
                    ),
                )
            except Leap0Error:
                responses.append(
                    FileDownloadResponse(
                        path=path,
                        content=None,
                        error="permission_denied",
                    ),
                )
            except Exception:  # noqa: BLE001
                responses.append(
                    FileDownloadResponse(
                        path=path,
                        content=None,
                        error="permission_denied",
                    ),
                )
            else:
                responses.append(
                    FileDownloadResponse(path=path, content=content, error=None),
                )
        return responses

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload files into the sandbox.

        Non-absolute paths return ``invalid_path`` without calling the API.
        Failures are reported per file via ``FileUploadResponse.error``.
        """
        responses: list[FileUploadResponse] = []
        for path, content in files:
            if not path.startswith("/"):
                responses.append(FileUploadResponse(path=path, error="invalid_path"))
                continue
            try:
                self._client.filesystem.write_file_bytes(
                    self._sandbox,
                    path=path,
                    content=content,
                )
            except Leap0APIError as exc:
                responses.append(
                    FileUploadResponse(
                        path=path,
                        error=self._map_filesystem_api_error(exc),
                    ),
                )
            except Leap0Error:
                responses.append(
                    FileUploadResponse(path=path, error="permission_denied"),
                )
            except Exception:  # noqa: BLE001
                responses.append(
                    FileUploadResponse(path=path, error="permission_denied"),
                )
            else:
                responses.append(FileUploadResponse(path=path, error=None))
        return responses

    @staticmethod
    def _map_filesystem_api_error(exc: Leap0APIError) -> FileOperationError:
        """Map Leap0 HTTP errors to ``FileOperationError`` literals."""
        if exc.status_code == _HTTP_NOT_FOUND:
            return "file_not_found"
        if exc.status_code == _HTTP_FORBIDDEN:
            return "permission_denied"
        combined = f"{exc.message} {exc.body or ''}".lower()
        if "is a directory" in combined:
            return "is_directory"
        return "permission_denied"
