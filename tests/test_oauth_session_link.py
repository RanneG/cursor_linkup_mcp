"""Regression: concurrent OAuth Add-account links must not drop account_ids."""
from __future__ import annotations

import importlib
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


class TestOAuthSessionLinkAccount(unittest.TestCase):
    def test_concurrent_link_keeps_both_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "stitch_auth.db"
            with patch.dict(os.environ, {"STITCH_AUTH_DB": str(db_path), "STITCH_GOOGLE_FERNET_KEY": "test-fernet-key-material"}):
                import stitch_auth.store as store

                importlib.reload(store)

                primary = store.google_account_upsert("owner@example.com", "sub-owner", "refresh-owner", None)
                second = store.google_account_upsert("second@example.com", "sub-second", "refresh-second", None)
                third = store.google_account_upsert("third@example.com", "sub-third", "refresh-third", None)
                sid = store.session_create([primary], "owner@example.com")

                barrier = threading.Barrier(2)
                errors: list[BaseException] = []

                def link(account_id: int, email: str) -> None:
                    try:
                        barrier.wait(timeout=5)
                        ok = store.session_link_account(sid, account_id, email)
                        if not ok:
                            raise AssertionError(f"link failed for {email}")
                    except BaseException as exc:  # noqa: BLE001 — collect thread failures
                        errors.append(exc)

                t1 = threading.Thread(target=link, args=(second, "second@example.com"))
                t2 = threading.Thread(target=link, args=(third, "third@example.com"))
                t1.start()
                t2.start()
                t1.join(timeout=10)
                t2.join(timeout=10)

                self.assertEqual(errors, [])
                sess = store.session_load(sid)
                assert sess is not None
                ids = {int(x) for x in sess["account_ids"]}
                self.assertEqual(ids, {primary, second, third})

                store._reset_connection_for_tests()

    def test_link_missing_session_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "stitch_auth.db"
            with patch.dict(os.environ, {"STITCH_AUTH_DB": str(db_path), "STITCH_GOOGLE_FERNET_KEY": "test-fernet-key-material"}):
                import stitch_auth.store as store

                importlib.reload(store)
                self.assertFalse(store.session_link_account("missing", 1, "a@example.com"))
                store._reset_connection_for_tests()

    def test_non_atomic_rmw_can_drop_an_account(self) -> None:
        """Document the old flask_routes pattern: unlocked RMW loses one writer."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "stitch_auth.db"
            with patch.dict(os.environ, {"STITCH_AUTH_DB": str(db_path), "STITCH_GOOGLE_FERNET_KEY": "test-fernet-key-material"}):
                import stitch_auth.store as store

                importlib.reload(store)

                primary = store.google_account_upsert("owner@example.com", "sub-owner", "refresh-owner", None)
                second = store.google_account_upsert("second@example.com", "sub-second", "refresh-second", None)
                third = store.google_account_upsert("third@example.com", "sub-third", "refresh-third", None)
                sid = store.session_create([primary], "owner@example.com")

                barrier = threading.Barrier(2)
                gate = threading.Event()

                def legacy_link(account_id: int, email: str, *, pause: bool) -> None:
                    sess = store.session_load(sid)
                    assert sess is not None
                    ids = list(sess.get("account_ids") or [])
                    if pause:
                        gate.set()
                        barrier.wait(timeout=5)
                    else:
                        barrier.wait(timeout=5)
                        gate.wait(timeout=5)
                    if account_id not in ids:
                        ids.append(account_id)
                    store.session_update(sid, ids, email)

                # Thread A reads first and pauses before write; B reads same snapshot then both write.
                t_a = threading.Thread(target=legacy_link, args=(second, "second@example.com"), kwargs={"pause": True})
                t_b = threading.Thread(target=legacy_link, args=(third, "third@example.com"), kwargs={"pause": False})
                t_a.start()
                t_b.start()
                t_a.join(timeout=10)
                t_b.join(timeout=10)

                sess = store.session_load(sid)
                assert sess is not None
                ids = {int(x) for x in sess["account_ids"]}
                # One of the newly linked accounts is missing under the legacy pattern.
                self.assertNotEqual(ids, {primary, second, third})
                self.assertIn(primary, ids)

                store._reset_connection_for_tests()


if __name__ == "__main__":
    unittest.main()
