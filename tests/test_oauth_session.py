"""OAuth session finalization — linking must fail closed if the original session is gone."""
from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestOauthSessionFinalize(unittest.TestCase):
    def test_fresh_sign_in_creates_session(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "stitch_auth.db"
            with patch.dict(os.environ, {"STITCH_AUTH_DB": str(db_path)}):
                import stitch_auth.oauth_session as oauth_session
                import stitch_auth.store as store

                importlib.reload(store)
                importlib.reload(oauth_session)

                aid = store.google_account_upsert("a@example.com", "sub-a", "refresh-a", None)
                sid, err = oauth_session.finalize_oauth_session(
                    linking_sid=None, account_id=aid, email="a@example.com"
                )
                self.assertIsNone(err)
                self.assertIsNotNone(sid)
                sess = store.session_load(sid or "")
                assert sess is not None
                self.assertEqual(sess["account_ids"], [aid])
                store._reset_connection_for_tests()

    def test_linking_appends_to_existing_session(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "stitch_auth.db"
            with patch.dict(os.environ, {"STITCH_AUTH_DB": str(db_path)}):
                import stitch_auth.oauth_session as oauth_session
                import stitch_auth.store as store

                importlib.reload(store)
                importlib.reload(oauth_session)

                a = store.google_account_upsert("a@example.com", "sub-a", "refresh-a", None)
                b = store.google_account_upsert("b@example.com", "sub-b", "refresh-b", None)
                sid = store.session_create([a], "a@example.com")

                out_sid, err = oauth_session.finalize_oauth_session(
                    linking_sid=sid, account_id=b, email="b@example.com"
                )
                self.assertIsNone(err)
                self.assertEqual(out_sid, sid)
                sess = store.session_load(sid)
                assert sess is not None
                self.assertEqual(sess["account_ids"], [a, b])
                self.assertEqual(sess["active_email"], "b@example.com")
                store._reset_connection_for_tests()

    def test_linking_with_dead_session_does_not_create_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "stitch_auth.db"
            with patch.dict(os.environ, {"STITCH_AUTH_DB": str(db_path)}):
                import stitch_auth.oauth_session as oauth_session
                import stitch_auth.store as store

                importlib.reload(store)
                importlib.reload(oauth_session)

                a = store.google_account_upsert("a@example.com", "sub-a", "refresh-a", None)
                b = store.google_account_upsert("b@example.com", "sub-b", "refresh-b", None)
                sid = store.session_create([a], "a@example.com")
                store.session_delete(sid)

                out_sid, err = oauth_session.finalize_oauth_session(
                    linking_sid=sid, account_id=b, email="b@example.com"
                )
                self.assertIsNone(out_sid)
                assert err is not None
                self.assertEqual(err["error"], "linking_session_expired")
                # No replacement session should exist for the dead linking id.
                self.assertIsNone(store.session_load(sid))
                store._reset_connection_for_tests()


if __name__ == "__main__":
    unittest.main()
