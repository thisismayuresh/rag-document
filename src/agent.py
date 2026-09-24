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

from config import settings
from llm.base import ChatClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions about a specific document.
You have access to a tool called `search_document` that searches the document for relevant text.

Rules:
- Always use `search_document` before answering a question about the document's content.
- Only answer using information returned by the tool. Do not use outside knowledge.
- If the tool does not return relevant information, say you could not find the answer in the document. Do not make anything up.
- When you answer using document content, mention the source page number(s).
"""


class Agent:
    def __init__(
        self,
        llm_client: ChatClient,
        tools_schema: list[dict[str, Any]],
        tool_functions: dict[str, Callable[..., str]],
    ) -> None:
        self._llm = llm_client
        self._tools_schema = tools_schema
        self._tool_functions = tool_functions
        self._conversation: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def ask(self, user_message: str) -> str:
        logger.info("Agent request started message_chars=%d", len(user_message))
        self._conversation.append({"role": "user", "content": user_message})

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
                    "Agent request completed rounds=%d answer_chars=%d",
                    round_number + 1,
                    len(answer),
                )
                return answer

            logger.info(
                "Agent decision round=%d action=tool_call tools=%s",
                round_number + 1,
                ",".join(call["function"]["name"] for call in tool_calls),
            )
            for call in tool_calls:
                self._conversation.append(
                    {"role": "tool", "content": self._execute_tool_call(call)}
                )

        logger.warning("Agent reached max tool rounds=%d", settings.max_tool_rounds)
        return "I'm having trouble finishing that - could you rephrase your question?"

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
