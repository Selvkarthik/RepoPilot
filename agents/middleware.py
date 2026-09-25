import logging

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage


logger = logging.getLogger(__name__)


class SearchLimitMiddleware(AgentMiddleware):
    """Prevent excessive repository-code searches in one agent run."""

    def wrap_tool_call(self, request, handler):
        if request.tool_call["name"] != "search_repository_code":
            return handler(request)

        search_calls = sum(
            1
            for message in request.state["messages"]
            if getattr(message, "tool_calls", None)
            and any(
                call.get("name") == "search_repository_code"
                for call in message.tool_calls
            )
        )

        logger.info(
            "Repository search requested: current_calls=%d max_calls=2",
            search_calls,
        )

        if search_calls >= 2:
            logger.warning(
                "Repository search limit reached: max_calls=2"
            )

            return ToolMessage(
                content=(
                    "You have already performed two repository searches. "
                    "Use the retrieved information to answer the question. "
                    "Do not perform another repository search."
                ),
                tool_call_id=request.tool_call["id"],
            )

        return handler(request)