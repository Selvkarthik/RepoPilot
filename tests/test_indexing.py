import unittest
from unittest.mock import MagicMock, patch

from rag.index_service import index_repository


class IndexingServiceTests(unittest.TestCase):
    def setUp(self):
        self.github_state = {
            "owner": "testowner",
            "repo": "testrepo",
            "branch": "main",
            "commit_sha": "commit-12345",
        }
        self.state_patch = patch(
            "rag.index_service.get_repository_state", return_value=self.github_state
        )
        self.stored_state_patch = patch(
            "rag.index_service.get_stored_repository_state"
        )
        self.files_patch = patch("rag.index_service.get_repository_files")
        self.repository_patch = patch("rag.index_service.CodeRepository")
        self.save_state_patch = patch("rag.index_service.save_repository_state")
        self.store_chunks_patch = patch("rag.index_service.store_chunks")
        self.split_patch = patch("rag.index_service.split_documents")
        self.create_docs_patch = patch("rag.index_service.create_documents")

        self.mock_get_state = self.state_patch.start()
        self.mock_get_stored_state = self.stored_state_patch.start()
        self.mock_get_files = self.files_patch.start()
        self.mock_repo_class = self.repository_patch.start()
        self.mock_save_state = self.save_state_patch.start()
        self.mock_store_chunks = self.store_chunks_patch.start()
        self.mock_split = self.split_patch.start()
        self.mock_create_docs = self.create_docs_patch.start()

        self.db = self.mock_repo_class.return_value
        self.addCleanup(patch.stopall)

    def test_unchanged_commit_does_not_reindex(self):
        """Unchanged commit SHA returns up_to_date without fetching files."""
        self.mock_get_stored_state.return_value = ("main", "commit-12345")

        result = index_repository("testowner", "testrepo")

        self.assertEqual(result["status"], "up_to_date")
        self.assertEqual(result["files_added"], 0)
        self.assertEqual(result["files_updated"], 0)
        self.assertEqual(result["files_deleted"], 0)
        self.mock_get_files.assert_not_called()

    def test_new_repository_is_indexed(self):
        """A new repository with no stored state indexes all files."""
        self.mock_get_stored_state.return_value = None
        self.db.get_file_hashes.return_value = {}

        file1 = {
            "path": "app/main.py",
            "content": "print('hello')",
            "language": "python",
            "content_hash": "hash-main-1",
        }
        file2 = {
            "path": "app/utils.py",
            "content": "def util(): pass",
            "language": "python",
            "content_hash": "hash-utils-1",
        }
        self.mock_get_files.return_value = [file1, file2]
        self.mock_split.side_effect = [[MagicMock()], [MagicMock()]]

        result = index_repository("testowner", "testrepo")

        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["files_added"], 2)
        self.assertEqual(result["files_updated"], 0)
        self.assertEqual(result["files_deleted"], 0)
        self.assertEqual(result["chunks_created"], 2)
        self.assertEqual(self.db.save_file.call_count, 2)
        self.mock_save_state.assert_called_once_with(self.github_state)

    def test_modified_files_are_reindexed(self):
        """Only modified files (differing content hash) are re-chunked and saved."""
        self.mock_get_stored_state.return_value = ("main", "old-commit")
        self.db.get_file_hashes.return_value = {
            "app/unchanged.py": "hash-same",
            "app/modified.py": "old-hash",
        }
        self.db.delete_file.return_value = 2

        file_unchanged = {
            "path": "app/unchanged.py",
            "content": "content",
            "language": "python",
            "content_hash": "hash-same",
        }
        file_modified = {
            "path": "app/modified.py",
            "content": "new content",
            "language": "python",
            "content_hash": "new-hash",
        }
        self.mock_get_files.return_value = [file_unchanged, file_modified]
        self.mock_split.return_value = [MagicMock(), MagicMock()]

        result = index_repository("testowner", "testrepo")

        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["files_added"], 0)
        self.assertEqual(result["files_updated"], 1)
        self.assertEqual(result["files_deleted"], 0)
        # Old chunks of modified file were deleted first
        self.db.delete_file.assert_called_once_with("testowner/testrepo", "app/modified.py")
        self.db.save_file.assert_called_once_with(
            repository="testowner/testrepo",
            file_path="app/modified.py",
            language="python",
            content_hash="new-hash",
        )

    def test_deleted_files_have_old_chunks_removed(self):
        """Files removed from GitHub have old chunks and file records deleted."""
        self.mock_get_stored_state.return_value = ("main", "old-commit")
        self.db.get_file_hashes.return_value = {
            "active.py": "hash-active",
            "deleted.py": "hash-deleted",
        }
        self.db.delete_file.return_value = 4

        self.mock_get_files.return_value = [
            {
                "path": "active.py",
                "content": "active",
                "language": "python",
                "content_hash": "hash-active",
            }
        ]

        result = index_repository("testowner", "testrepo")

        self.assertEqual(result["files_deleted"], 1)
        self.assertEqual(result["chunks_deleted"], 4)
        self.db.delete_file.assert_called_once_with("testowner/testrepo", "deleted.py")
        self.mock_save_state.assert_called_once_with(self.github_state)


if __name__ == "__main__":
    unittest.main()
