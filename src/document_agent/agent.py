"""A minimal, explicit tool-calling agent loop.

Deliberately hand-written instead of pulling in a framework, so every step
stays visible: ask the model -> does it want a tool? -> run the tool ->
feed the result back -> ask again -> ... -> final answer.

Note this class depends on `ChatClient` (an interface), not on Ollama.
Handing it a different implementation is the entire migration path to a
different model or provider later.
"""

import json
import logging
from typing import Any, Callable

from document_agent.config import settings
from document_agent.data_models import AgentResponse, Citation
from document_agent.llm.base import ChatClient
from document_agent.tools import SEARCH_TOOL_NAME, parse_citations

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a document question-answering assistant.
The user has uploaded one or more documents to this session.
You have two tools:
- `list_documents`: lists the documents available in this session.
- `search_document`: searches those documents and returns matching chunks with document names and page numbers.

Rules:
- Before answering any question about document content, use the tools. Call `list_documents` if you are unsure which documents exist, then `search_document` with a focused query.
- Answer ONLY from text returned by `search_document`. Never use outside knowledge to answer questions about the documents.
- If the search results do not contain the answer, say clearly that you could not find it in the uploaded documents. Do not guess, invent, or fill gaps with general knowledge.
- When you answer from document content, cite the source document name and page number(s) for each claim.
- For questions unrelated to the documents (greetings, meta questions about the chat), answer briefly and naturally without calling the tools.
"""


class Agent:
    def __init__(
        self,
        llm_client: ChatClient,
        tools_schema: list[dict[str, Any]],
        tool_functions: dict[str, Callable[..., str]],
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        self._llm = llm_client
        self._tools_schema = tools_schema
        self._tool_functions = tool_functions
        self._conversation: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    def ask(self, user_message: str) -> AgentResponse:
        """Answer one user message, collecting citations from document searches."""
        logger.info("Agent request started message_chars=%d", len(user_message))
        self._conversation.append({"role": "user", "content": user_message})
        citations: list[Citation] = []

        for round_number in range(settings.max_tool_rounds):
            logger.debug("Starting agent round=%d", round_number + 1)
            reply = self._llm.chat(self._conversation, tools=self._tools_schema)
            self._conversation.append(reply)

            tool_calls = reply.get("tool_calls")
            if not tool_calls:
                logger.info(
                    "Agent decision round=%d action=final_answer",
                    round_number + 1,
                )
                answer = reply.get("content", "")
                logger.info(
                    "Agent request completed rounds=%d answer_chars=%d citations=%d",
                    round_number + 1,
                    len(answer),
                    len(citations),
                )
                return AgentResponse(answer=answer, citations=_dedupe(citations))

            logger.info(
                "Agent decision round=%d action=tool_call tools=%s",
                round_number + 1,
                ",".join(call["function"]["name"] for call in tool_calls),
            )
            for call in tool_calls:
                result = self._execute_tool_call(call)
                if call["function"]["name"] == SEARCH_TOOL_NAME:
                    citations.extend(parse_citations(result))
                self._conversation.append({"role": "tool", "content": result})

        logger.warning("Agent reached max tool rounds=%d", settings.max_tool_rounds)
        return AgentResponse(
            answer="I'm having trouble finishing that - could you rephrase your question?",
            citations=[],
        )

    def _execute_tool_call(self, call: dict[str, Any]) -> str:
        name = call["function"]["name"]
        logger.info("Tool execution started tool=%s", name)
        raw_arguments = call["function"].get("arguments", {})
        arguments = (
            raw_arguments
            if isinstance(raw_arguments, dict)
            else json.loads(raw_arguments)
        )

        tool_function = self._tool_functions.get(name)
        if tool_function is None:
            return f"Error: unknown tool '{name}'"

        try:
            result = tool_function(**arguments)
            logger.info(
                "Tool execution completed tool=%s result_chars=%d",
                name,
                len(result),
            )
            return result
        except (
            Exception
        ) as exc:  # noqa: BLE001 - report tool failures to the model, don't crash the agent
            logger.exception("Tool '%s' raised an error", name)
            return f"Error running tool '{name}': {exc}"


def _dedupe(citations: list[Citation]) -> list[Citation]:
    """Drop repeated (document, page) pairs, keeping first-seen order."""
    seen: set[tuple[str, int]] = set()
    unique: list[Citation] = []
    for citation in citations:
        key = (citation.document_name, citation.page_number)
        if key not in seen:
            seen.add(key)
            unique.append(citation)
    return unique
