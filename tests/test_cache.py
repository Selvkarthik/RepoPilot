import unittest
from unittest.mock import MagicMock, patch

from rag.cache import build_cache_key, get_cached_result, set_cached_result
from tools.github_tools import search_repository_code


class CacheKeyTests(unittest.TestCase):
    def test_cache_key_deterministic_and_normalized(self):
        key1 = build_cache_key("owner/repo", "sha123", "How does auth work?")
        key2 = build_cache_key("owner/repo", "sha123", "  how does auth work?  ")
        self.assertEqual(key1, key2)

    def test_cache_key_different_for_different_queries(self):
        key1 = build_cache_key("owner/repo", "sha123", "query one")
        key2 = build_cache_key("owner/repo", "sha123", "query two")
        self.assertNotEqual(key1, key2)

    def test_cache_key_different_for_different_commits(self):
        key1 = build_cache_key("owner/repo", "sha123", "query")
        key2 = build_cache_key("owner/repo", "sha456", "query")
        self.assertNotEqual(key1, key2)

    def test_cache_key_different_for_different_repositories(self):
        key1 = build_cache_key("owner/repo1", "sha123", "query")
        key2 = build_cache_key("owner/repo2", "sha123", "query")
        self.assertNotEqual(key1, key2)


class CacheExecutionTests(unittest.TestCase):
    def setUp(self):
        self.fake_cache = {}

    @patch("tools.github_tools.get_code_retriever")
    @patch("tools.github_tools.CodeRepository")
    @patch("tools.github_tools.get_cached_result")
    @patch("tools.github_tools.set_cached_result")
    def test_cache_miss_then_hit_flow(
        self, mock_set_cache, mock_get_cache, mock_repo_class, mock_retriever_func
    ):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_repository_commit.return_value = "commit-abc"

        retriever = MagicMock()
        mock_retriever_func.return_value = retriever
        doc = MagicMock()
        doc.metadata = {
            "file_path": "main.py",
            "language": "python",
            "chunk_index": 0,
        }
        doc.page_content = "def hello(): pass"
        retriever.invoke.return_value = [doc]

        # 1. First identical query -> MISS
        mock_get_cache.return_value = None
        result1 = search_repository_code.invoke(
            {"query": "where is hello", "repository": "owner/repo"}
        )

        mock_get_cache.assert_called_once()
        retriever.invoke.assert_called_once_with("where is hello")
        mock_set_cache.assert_called_once()
        self.assertIn("def hello(): pass", result1)

        # 2. Same repository + same commit + same query -> HIT
        mock_get_cache.reset_mock()
        mock_set_cache.reset_mock()
        retriever.invoke.reset_mock()

        # Simulate cache now having the value
        mock_get_cache.return_value = result1

        result2 = search_repository_code.invoke(
            {"query": "where is hello", "repository": "owner/repo"}
        )

        mock_get_cache.assert_called_once()
        retriever.invoke.assert_not_called()
        self.assertEqual(result1, result2)

        # 3. Different query -> MISS
        mock_get_cache.reset_mock()
        retriever.invoke.reset_mock()
        mock_get_cache.return_value = None

        search_repository_code.invoke(
            {"query": "different question", "repository": "owner/repo"}
        )
        retriever.invoke.assert_called_once_with("different question")

        # 4. New commit SHA -> MISS
        mock_get_cache.reset_mock()
        retriever.invoke.reset_mock()
        mock_repo.get_repository_commit.return_value = "commit-def"
        mock_get_cache.return_value = None

        search_repository_code.invoke(
            {"query": "where is hello", "repository": "owner/repo"}
        )
        retriever.invoke.assert_called_once_with("where is hello")

    def test_cache_gracefully_handles_redis_connection_error(self):
        with patch("rag.cache.cache") as mock_cache:
            mock_cache.get.side_effect = ConnectionError("Redis unreachable")
            mock_cache.setex.side_effect = ConnectionError("Redis unreachable")

            # get_cached_result falls back to None instead of raising
            result = get_cached_result("some_key")
            self.assertIsNone(result)

            # set_cached_result logs warning instead of raising
            try:
                set_cached_result("some_key", {"data": 123})
            except Exception as e:
                self.fail(f"set_cached_result should not raise on Redis failure: {e}")


if __name__ == "__main__":
    unittest.main()
