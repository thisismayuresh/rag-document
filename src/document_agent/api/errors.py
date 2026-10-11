"""Structured API errors.

Every intentional failure the routes raise goes through ApiError so the
frontend always receives the same shape:

    {"error": {"code": "document_too_large", "message": "..."}}

The code is stable and machine-readable; the message is for humans.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from requests import RequestException

from document_agent.sessions import UnknownDocumentError, UnknownSessionError

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """An expected failure with a status code and a stable error code."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def register_exception_handlers(app: FastAPI) -> None:
    """Teach the app how to turn exceptions into the standard error shape."""

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        logger.info(
            "API error method=%s path=%s code=%s message=%s",
            request.method,
            request.url.path,
            exc.code,
            exc.message,
        )
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(UnknownSessionError)
    async def handle_unknown_session(
        request: Request, exc: UnknownSessionError
    ) -> JSONResponse:
        return _error_response(
            404,
            "unknown_session",
            "This session no longer exists. Start a new session and upload "
            "your documents again.",
        )

    @app.exception_handler(UnknownDocumentError)
    async def handle_unknown_document(
        request: Request, exc: UnknownDocumentError
    ) -> JSONResponse:
        return _error_response(
            404,
            "unknown_document",
            f"Document '{exc.document_name}' is not part of this session.",
        )

    @app.exception_handler(RequestException)
    async def handle_upstream_failure(
        request: Request, exc: RequestException
    ) -> JSONResponse:
        logger.exception(
            "Upstream service failure method=%s path=%s",
            request.method,
            request.url.path,
        )
        return _error_response(
            502,
            "upstream_unavailable",
            "A required service (Ollama or ChromaDB) did not respond. Check "
            "that it is running and try again.",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled error method=%s path=%s",
            request.method,
            request.url.path,
        )
        return _error_response(
            500, "internal_error", "Something went wrong handling this request."
        )


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": {"code": code, "message": message}}
    )
