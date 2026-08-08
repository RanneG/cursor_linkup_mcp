"""Regression: concurrent first-time Fernet key creation must not lose tokens."""
from __future__ import annotations

import importlib
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


class TestFernetKeyCreate(unittest.TestCase):
    def test_concurrent_first_encrypt_uses_single_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            db_path = home / ".stitch" / "stitch_auth.db"
            env = {
                "STITCH_AUTH_DB": str(db_path),
                "STITCH_GOOGLE_FERNET_KEY": "",
                "HOME": str(home),
                "USERPROFILE": str(home),
            }
            with patch.dict(os.environ, env, clear=False), patch.object(Path, "home", return_value=home):
                import stitch_auth.store as store

                importlib.reload(store)

                workers = 8
                barrier = threading.Barrier(workers)
                errors: list[str] = []

                def worker(i: int) -> None:
                    try:
                        barrier.wait(timeout=5)
                        token = f"refresh-token-{i}"
                        aid = store.google_account_upsert(
                            f"user{i}@example.com",
                            f"sub-{i}",
                            token,
                            None,
                        )
                        row = store.google_account_by_id(aid)
                        assert row is not None
                        plain = store.decrypt_refresh(row)
                        if plain != token:
                            errors.append(f"mismatch i={i}")
                    except Exception as exc:  # noqa: BLE001 - collect for assertion
                        errors.append(f"i={i} {type(exc).__name__}: {exc}")

                threads = [threading.Thread(target=worker, args=(i,)) for i in range(workers)]
                for th in threads:
                    th.start()
                for th in threads:
                    th.join(timeout=10)

                key_path = home / ".stitch" / ".google_fernet_key"
                self.assertTrue(key_path.is_file(), "fernet key file missing")
                self.assertGreaterEqual(key_path.stat().st_size, 32)

                for i in range(workers):
                    row = store.google_account_by_email(f"user{i}@example.com")
                    self.assertIsNotNone(row, f"missing account user{i}")
                    self.assertEqual(store.decrypt_refresh(row), f"refresh-token-{i}")

                store._reset_connection_for_tests()
                self.assertEqual(errors, [], errors)

    def test_second_caller_reuses_existing_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            db_path = home / ".stitch" / "stitch_auth.db"
            env = {
                "STITCH_AUTH_DB": str(db_path),
                "STITCH_GOOGLE_FERNET_KEY": "",
                "HOME": str(home),
                "USERPROFILE": str(home),
            }
            with patch.dict(os.environ, env, clear=False), patch.object(Path, "home", return_value=home):
                import stitch_auth.store as store

                importlib.reload(store)

                store.google_account_upsert("a@example.com", "sub-a", "token-a", None)
                first_key = (home / ".stitch" / ".google_fernet_key").read_bytes()
                store.google_account_upsert("b@example.com", "sub-b", "token-b", None)
                second_key = (home / ".stitch" / ".google_fernet_key").read_bytes()

                self.assertEqual(first_key, second_key)
                row_a = store.google_account_by_email("a@example.com")
                row_b = store.google_account_by_email("b@example.com")
                self.assertEqual(store.decrypt_refresh(row_a), "token-a")
                self.assertEqual(store.decrypt_refresh(row_b), "token-b")
                store._reset_connection_for_tests()


if __name__ == "__main__":
    unittest.main()
