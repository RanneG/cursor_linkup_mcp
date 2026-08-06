"""Round-trip tests for encrypted face enrollment storage (no DeepFace)."""
from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


class TestFaceStorage(unittest.TestCase):
    def test_save_load_delete(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fake_home = Path(td) / "h"
            fake_home.mkdir()
            dbdir = fake_home / "stitch" / "face_db"
            with patch.dict(os.environ, {"STITCH_FACE_DB_DIR": str(dbdir)}):
                import face_verification.storage as storage

                importlib.reload(storage)

                email = "User@Example.com"
                emb = [np.random.randn(128).astype(float).tolist()]
                storage.save_enrollment(email, emb, model_name="Facenet")
                self.assertTrue(storage.is_enrolled(email))
                rec = storage.load_enrollment(email)
                self.assertIsNotNone(rec)
                assert rec is not None
                self.assertEqual(len(rec.embeddings), 1)
                self.assertTrue(storage.delete_enrollment(email))
                self.assertFalse(storage.is_enrolled(email))

    def test_truncated_enrollment_blob_is_unenrollable(self) -> None:
        """Characterize the failure mode: truncate leaves is_enrolled True but load None."""
        with tempfile.TemporaryDirectory() as td:
            dbdir = Path(td) / "face_db"
            with patch.dict(os.environ, {"STITCH_FACE_DB_DIR": str(dbdir)}):
                import face_verification.storage as storage

                importlib.reload(storage)

                email = "user@example.com"
                emb = [np.random.randn(128).astype(float).tolist()]
                storage.save_enrollment(email, emb, model_name="Facenet")
                path = storage._path_for_email(email)
                path.write_bytes(b"")  # simulate crash after O_TRUNC, before write completes
                self.assertTrue(storage.is_enrolled(email))
                self.assertIsNone(storage.load_enrollment(email))

    def test_failed_touch_preserves_prior_enrollment(self) -> None:
        """touch_last_verified must not destroy the blob if the atomic write fails."""
        with tempfile.TemporaryDirectory() as td:
            dbdir = Path(td) / "face_db"
            with patch.dict(os.environ, {"STITCH_FACE_DB_DIR": str(dbdir)}):
                import face_verification.storage as storage

                importlib.reload(storage)

                email = "user@example.com"
                emb = [np.random.randn(128).astype(float).tolist()]
                storage.save_enrollment(email, emb, model_name="Facenet")
                before = storage._path_for_email(email).read_bytes()

                with patch.object(storage.os, "replace", side_effect=OSError("disk full")):
                    with self.assertRaises(OSError):
                        storage.touch_last_verified(email)

                after = storage._path_for_email(email).read_bytes()
                self.assertEqual(before, after)
                rec = storage.load_enrollment(email)
                self.assertIsNotNone(rec)
                assert rec is not None
                self.assertEqual(len(rec.embeddings), 1)
                self.assertIsNone(rec.last_verified)

    def test_save_enrollment_uses_os_replace(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dbdir = Path(td) / "face_db"
            with patch.dict(os.environ, {"STITCH_FACE_DB_DIR": str(dbdir)}):
                import face_verification.storage as storage

                importlib.reload(storage)

                email = "user@example.com"
                emb = [np.random.randn(32).astype(float).tolist()]
                with patch.object(storage.os, "replace", wraps=storage.os.replace) as mocked:
                    storage.save_enrollment(email, emb, model_name="Facenet")
                    mocked.assert_called()
                self.assertIsNotNone(storage.load_enrollment(email))


if __name__ == "__main__":
    unittest.main()
