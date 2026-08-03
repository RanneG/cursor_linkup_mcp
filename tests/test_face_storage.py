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

    def test_truncated_master_key_does_not_rotate_when_enrollments_exist(self) -> None:
        """Crash mid-write can leave .master_key empty; must not mint a new key."""
        with tempfile.TemporaryDirectory() as td:
            dbdir = Path(td) / "face_db"
            with patch.dict(os.environ, {"STITCH_FACE_DB_DIR": str(dbdir)}):
                import face_verification.storage as storage

                importlib.reload(storage)

                email = "ranne@example.com"
                emb = [np.random.randn(128).astype(float).tolist()]
                storage.save_enrollment(email, emb, model_name="Facenet")
                key_path = dbdir / ".master_key"
                good_key = key_path.read_bytes()
                self.assertGreaterEqual(len(good_key), 32)

                # Simulate truncated key after crash during rewrite.
                key_path.write_bytes(b"")

                with self.assertRaises(storage.FaceKeyError):
                    storage.load_enrollment(email)

                # Original key bytes must still be required — empty key must not be replaced.
                self.assertEqual(key_path.read_bytes(), b"")
                self.assertTrue(storage.is_enrolled(email))

                # Restore key → enrollment still decrypts.
                key_path.write_bytes(good_key)
                rec = storage.load_enrollment(email)
                self.assertIsNotNone(rec)

    def test_truncated_master_key_ok_to_recreate_when_db_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dbdir = Path(td) / "face_db"
            with patch.dict(os.environ, {"STITCH_FACE_DB_DIR": str(dbdir)}):
                import face_verification.storage as storage

                importlib.reload(storage)

                dbdir.mkdir(parents=True, exist_ok=True)
                (dbdir / ".master_key").write_bytes(b"short")
                material = storage._master_key_material()
                self.assertEqual(len(material), 32)
                self.assertEqual((dbdir / ".master_key").read_bytes(), material)


if __name__ == "__main__":
    unittest.main()
