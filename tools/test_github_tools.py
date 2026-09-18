import unittest
from unittest.mock import patch

from tools.github_tools import search_repository_code


class IndexGithubRepositoryToolTests(unittest.TestCase):

    @patch("tools.github_tools.get_code_retriever")
    @patch("tools.github_tools.run_index")
    def test_search_synchronizes_before_retrieving(self, run_index, get_code_retriever):
        run_index.return_value = {"status": "up_to_date"}
        retriever = get_code_retriever.return_value
        retriever.invoke.return_value = []

        result = search_repository_code.invoke(
            {"query": "Where is authentication configured?", "repository": "owner/repo"}
        )

        run_index.assert_called_once_with("owner", "repo")
        get_code_retriever.assert_called_once_with("owner/repo", k=3)
        retriever.invoke.assert_called_once_with("Where is authentication configured?")
        self.assertEqual(result, "The repository is current, but no relevant code was found.")

    @patch("tools.github_tools.get_code_retriever")
    @patch("tools.github_tools.run_index")
    def test_search_reports_an_empty_newly_synchronized_repository(
        self, run_index, get_code_retriever
    ):
        run_index.return_value = {"status": "updated"}
        get_code_retriever.return_value.invoke.return_value = []

        result = search_repository_code.invoke(
            {"query": "Where is authentication configured?", "repository": "owner/repo"}
        )

        self.assertEqual(result, "Repository was synchronized, but no searchable code was found.")

    def test_search_requires_owner_repository_format(self):
        result = search_repository_code.invoke(
            {"query": "Where is authentication configured?", "repository": "repo"}
        )

        self.assertEqual(
            result,
            "Unable to prepare repo for code search: Repository must use the 'owner/repository' format.",
        )


if __name__ == "__main__":
    unittest.main()
