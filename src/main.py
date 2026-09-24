"""Terminal entry point for ingesting a PDF and chatting about it."""

import logging
import os
import sys

import requests

from agent import Agent
from embeddings.factory import create_embedding_client
from ingestion import ingest_pdf
from llm.factory import create_chat_client
from logging_config import configure_logging
from tools import Tools
from vector_store import VectorStore

configure_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    """Build the application services and start the terminal chat loop."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    logger.info("Starting CLI document=%s", os.path.basename(pdf_path))
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    embedding_client = create_embedding_client()
    vector_store = VectorStore()

    if vector_store.is_empty():
        chunk_count = ingest_pdf(pdf_path, vector_store, embedding_client)
        logger.info("Document ingestion completed chunks=%d", chunk_count)
        print(f"Ingested {chunk_count} chunks from {pdf_path}\n")
    else:
        print("Existing collection found in Chroma - skipping ingestion.")
        print("(Reset the Chroma collection if you want to re-ingest.)\n")

    tools = Tools(vector_store, embedding_client)
    agent = Agent(
        llm_client=create_chat_client(),
        tools_schema=[tools.schema],
        tool_functions={tools.name: tools.search_document},
    )

    _run_chat_loop(agent, pdf_path)


def _run_chat_loop(agent: Agent, pdf_path: str) -> None:
    """Read questions until the user exits and print each answer."""
    print("=" * 40)
    print("     Local Document AI Agent")
    print("=" * 40)
    print(f"Document: {pdf_path}")
    print("Ask a question or type 'exit'.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            logger.info("Chat session ended")
            break
        if not user_input:
            continue

        try:
            answer = agent.ask(user_input)
        except requests.RequestException as exc:
            logger.error("Ollama request failed: %s", exc)
            print(
                "\nAI: Ollama did not respond. Check that Ollama is running "
                "and try again.\n"
            )
            continue
        print(f"\nAI:\n{answer}\n")


if __name__ == "__main__":
    main()
