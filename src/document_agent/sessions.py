"""In-memory session registry.

A session owns one conversation (an Agent) and one document collection in
ChromaDB. The registry is the only place sessions are created, looked up,
and destroyed. State lives in process memory: restarting the API starts
fresh sessions (uploaded PDF files remain on disk under documents/).

Everything here can be called from FastAPI's threadpool, so mutations are
guarded by a lock.
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from document_agent.agent import Agent
from document_agent.config import settings
from document_agent.data_models import DocumentInfo
from document_agent.embeddings.base import EmbeddingProvider
from document_agent.llm.base import ChatClient
from document_agent.tools import Tools
from document_agent.vector_store import VectorStore

logger = logging.getLogger(__name__)


class UnknownSessionError(Exception):
    """Raised when a session id does not exist (anymore)."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Unknown session: {session_id}")
        self.session_id = session_id


class UnknownDocumentError(Exception):
    """Raised when a session does not contain the named document."""

    def __init__(self, session_id: str, document_name: str) -> None:
        super().__init__(f"Unknown document in session {session_id}: {document_name}")
        self.session_id = session_id
        self.document_name = document_name


@dataclass
class SessionState:
    """One user session: a conversation plus its private documents."""

    id: str
    collection_name: str
    agent: Agent
    vector_store: VectorStore
    embedding_client: EmbeddingProvider
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    documents: list[DocumentInfo] = field(default_factory=list)

    def find_document(self, name: str) -> DocumentInfo | None:
        return next((doc for doc in self.documents if doc.name == name), None)


class SessionRegistry:
    """Creates and tracks sessions for the HTTP API."""

    def __init__(
        self, embedding_client: EmbeddingProvider, chat_client: ChatClient
    ) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, SessionState] = {}
        self._embedding_client = embedding_client
        self._chat_client = chat_client

    def create(self) -> SessionState:
        session_id = uuid.uuid4().hex
        collection_name = f"session_{session_id}"

        vector_store = VectorStore(collection_name)
        tools = Tools(vector_store, self._embedding_client)
        agent = Agent(
            llm_client=self._chat_client,
            tools_schema=tools.schemas(),
            tool_functions=tools.registry(),
        )
        session = SessionState(
            id=session_id,
            collection_name=collection_name,
            agent=agent,
            vector_store=vector_store,
            embedding_client=self._embedding_client,
        )

        with self._lock:
            self._sessions[session_id] = session

        logger.info("Session created id=%s collection=%s", session_id, collection_name)
        return session

    def get(self, session_id: str) -> SessionState:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise UnknownSessionError(session_id)
        return session

    def add_document(self, session: SessionState, document: DocumentInfo) -> None:
        with self._lock:
            session.documents.append(document)
        logger.info(
            "Document registered session=%s name=%s chunks=%d",
            session.id,
            document.name,
            document.chunk_count,
        )

    def remove_document(self, session: SessionState, name: str) -> DocumentInfo:
        """Drop a document from the session and from the vector store."""
        with self._lock:
            document = session.find_document(name)
            if document is None:
                raise UnknownDocumentError(session.id, name)
            session.documents.remove(document)

        session.vector_store.delete_document(name)
        logger.info("Document removed session=%s name=%s", session.id, name)
        return document

    def delete(self, session_id: str) -> None:
        """Forget a session and delete its collection from ChromaDB."""
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            raise UnknownSessionError(session_id)

        session.vector_store.drop_collection()
        logger.info("Session deleted id=%s", session_id)
