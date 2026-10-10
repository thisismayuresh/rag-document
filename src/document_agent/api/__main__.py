"""`python -m document_agent.api` and the `document-agent-api` command."""

import argparse


def run() -> None:
    """Start the HTTP API with uvicorn.

    Examples:
        document-agent-api
        document-agent-api --reload
        document-agent-api --port 9000
    """
    parser = argparse.ArgumentParser(
        prog="document-agent-api",
        description="Run the Local Document Agent HTTP API.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--reload",
        action="store_true",
        help="restart on code changes (development only)",
    )
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        "document_agent.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    run()
