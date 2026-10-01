from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from langchain_core.messages import ToolMessage
from agents.middleware import SearchLimitMiddleware, MAX_RESULT_CHARS


class MiddlewareTests(unittest.TestCase):
    def setUp(self):
        self.middleware = SearchLimitMiddleware()

    def _create_request(self, tool_name: str, previous_searches: int = 0):
        messages = []
        for i in range(previous_searches):
            msg = SimpleNamespace(
                tool_calls=[{"name": "search_repository_code", "id": f"call_{i}"}]
            )
            messages.append(msg)

        request = SimpleNamespace(
            tool_call={"name": tool_name, "id": "current_call_id"},
            state={"messages": messages},
        )
        return request

    def test_first_search_is_allowed(self):
        request = self._create_request("search_repository_code", previous_searches=0)
        handler = MagicMock(return_value=ToolMessage(content="results", tool_call_id="current_call_id"))

        response = self.middleware.wrap_tool_call(request, handler)

        handler.assert_called_once_with(request)
        self.assertEqual(response.content, "results")

    def test_second_search_is_allowed(self):
        request = self._create_request("search_repository_code", previous_searches=1)
        handler = MagicMock(return_value=ToolMessage(content="second results", tool_call_id="current_call_id"))

        response = self.middleware.wrap_tool_call(request, handler)

        handler.assert_called_once_with(request)
        self.assertEqual(response.content, "second results")

    def test_third_search_is_blocked(self):
        request = self._create_request("search_repository_code", previous_searches=2)
        handler = MagicMock()

        response = self.middleware.wrap_tool_call(request, handler)

        # Handler should NOT be called because limit was reached
        handler.assert_not_called()
        self.assertIsInstance(response, ToolMessage)
        self.assertIn("already performed two repository searches", response.content)
        self.assertEqual(response.tool_call_id, "current_call_id")

    def test_unrelated_tool_remains_allowed(self):
        request = self._create_request("get_repository_structure", previous_searches=5)
        handler = MagicMock(return_value="dir structure")

        response = self.middleware.wrap_tool_call(request, handler)

        handler.assert_called_once_with(request)
        self.assertEqual(response, "dir structure")

    def test_oversized_tool_output_is_truncated(self):
        request = self._create_request("search_repository_code", previous_searches=0)
        oversized_text = "A" * (MAX_RESULT_CHARS + 500)
        handler = MagicMock(
            return_value=ToolMessage(content=oversized_text, tool_call_id="current_call_id")
        )

        response = self.middleware.wrap_tool_call(request, handler)

        self.assertIn("[Result truncated]", response.content)
        self.assertTrue(len(response.content) <= MAX_RESULT_CHARS + len("\n[Result truncated]"))


if __name__ == "__main__":
    unittest.main()
