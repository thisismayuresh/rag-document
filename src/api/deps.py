"""Shared FastAPI dependencies."""

from fastapi import Request

from sessions import SessionRegistry


def get_registry(request: Request) -> SessionRegistry:
    """The session registry the lifespan handler attached to the app."""
    return request.app.state.sessions
