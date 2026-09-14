import unittest
from unittest.mock import MagicMock, patch

from rag.index_service import index_repository


class IndexRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.github_state = {
            "owner": "owner",
            "repo": "repo",
            "branch": "main",
            "commit_sha": "new-commit",
        }
        self.state_patch = patch(
            "rag.index_service.get_repository_state", return_value=self.github_state
        )
        self.stored_state_patch = patch(
            "rag.index_service.get_stored_repository_state", return_value=("main", "old-commit")
        )
        self.files_patch = patch("rag.index_service.get_repository_files")
        self.repository_patch = patch("rag.index_service.CodeRepository")
        self.save_state_patch = patch("rag.index_service.save_repository_state")

        self.get_state = self.state_patch.start()
        self.get_stored_state = self.stored_state_patch.start()
        self.get_files = self.files_patch.start()
        self.repository_class = self.repository_patch.start()
        self.save_state = self.save_state_patch.start()
        self.db = self.repository_class.return_value

        self.addCleanup(patch.stopall)

    def test_returns_zero_counts_when_repository_is_up_to_date(self):
        self.get_stored_state.return_value = ("main", "new-commit")

        result = index_repository("owner", "repo")

        self.assertEqual(
            result,
            {
                "repository": "owner/repo",
                "status": "up_to_date",
                "files_added": 0,
                "files_updated": 0,
                "files_deleted": 0,
                "chunks_created": 0,
                "chunks_deleted": 0,
            },
        )
        self.get_files.assert_not_called()

    def test_deletes_removed_file_and_reports_removed_chunks(self):
        self.get_files.return_value = []
        self.db.get_file_hashes.return_value = {"removed.py": "old-hash"}
        self.db.delete_file.return_value = 3

        result = index_repository("owner", "repo")

        self.db.delete_file.assert_called_once_with("owner/repo", "removed.py")
        self.save_state.assert_called_once_with(self.github_state)
        self.assertEqual(result["files_deleted"], 1)
        self.assertEqual(result["chunks_deleted"], 3)
        self.assertEqual(result["files_added"], 0)
        self.assertEqual(result["files_updated"], 0)
        self.assertEqual(result["chunks_created"], 0)

    @patch("rag.index_service.store_chunks")
    @patch("rag.index_service.split_documents")
    @patch("rag.index_service.create_documents")
    def test_reports_added_updated_and_deleted_files(
        self, create_documents, split_documents, store_chunks
    ):
        new_file = {
            "path": "new.py", "content": "new", "language": "python", "content_hash": "new-hash"
        }
        changed_file = {
            "path": "changed.py", "content": "changed", "language": "python", "content_hash": "new-changed-hash"
        }
        self.get_files.return_value = [new_file, changed_file]
        self.db.get_file_hashes.return_value = {
            "changed.py": "old-changed-hash", "removed.py": "removed-hash"
        }
        self.db.delete_file.side_effect = [5, 4]
        split_documents.side_effect = [[MagicMock(), MagicMock()], [MagicMock()]]

        result = index_repository("owner", "repo")

        self.assertEqual(result["files_added"], 1)
        self.assertEqual(result["files_updated"], 1)
        self.assertEqual(result["files_deleted"], 1)
        self.assertEqual(result["chunks_created"], 3)
        self.assertEqual(result["chunks_deleted"], 9)
        self.assertEqual(self.db.save_file.call_count, 2)
        self.assertEqual(store_chunks.call_count, 2)


if __name__ == "__main__":
    unittest.main()
