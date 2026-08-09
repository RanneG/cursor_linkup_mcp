"""Unit tests for pure stitch_auth helpers (no OAuth/Gmail network calls)."""
from __future__ import annotations

import importlib
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import flask  # noqa: F401

    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False

if _HAS_FLASK:
    from stitch_auth.flask_routes import (
        _html_callback_page,
        _json_for_html_script,
        _redirect_origin_ipv4,
        register_stitch_auth_routes,
    )


@unittest.skipUnless(_HAS_FLASK, "stitch-bridge extra not installed")
class RedirectOriginIpv4Tests(unittest.TestCase):
    def test_empty_falls_back_to_bridge_default(self) -> None:
        self.assertEqual(_redirect_origin_ipv4(""), "http://127.0.0.1:8765")

    def test_localhost_rewritten_to_ipv4_with_port(self) -> None:
        self.assertEqual(_redirect_origin_ipv4("http://localhost:1420"), "http://127.0.0.1:1420")

    def test_localhost_without_port(self) -> None:
        self.assertEqual(_redirect_origin_ipv4("http://localhost"), "http://127.0.0.1")

    def test_non_localhost_passthrough(self) -> None:
        self.assertEqual(_redirect_origin_ipv4("http://127.0.0.1:5173/"), "http://127.0.0.1:5173")
        self.assertEqual(_redirect_origin_ipv4("https://example.com"), "https://example.com")

    def test_missing_scheme_gets_http(self) -> None:
        self.assertEqual(_redirect_origin_ipv4("localhost:8080"), "http://127.0.0.1:8080")


@unittest.skipUnless(_HAS_FLASK, "stitch-bridge extra not installed")
class HtmlCallbackXssTests(unittest.TestCase):
    def test_json_for_html_script_escapes_script_breakout(self) -> None:
        encoded = _json_for_html_script({"error": "</script><script>alert(1)</script>"})
        self.assertNotIn("</script>", encoded)
        self.assertIn("\\u003c/script\\u003e", encoded)

    def test_callback_page_does_not_break_out_of_script(self) -> None:
        html = _html_callback_page(
            "http://localhost:1420",
            {
                "ok": False,
                "error": "</script><script>alert(1)</script>",
                "error_description": "<img src=x onerror=alert(1)>",
            },
        )
        # Only the intentional closing tag of our script block should remain literal.
        closers = [m.start() for m in re.finditer(r"</script>", html, flags=re.IGNORECASE)]
        self.assertEqual(len(closers), 1)
        self.assertIn("\\u003c/script\\u003e", html)
        self.assertIn("\\u003cimg", html)

    def test_error_query_param_reflected_safely_via_callback_route(self) -> None:
        app = flask.Flask(__name__)
        register_stitch_auth_routes(app)
        client = app.test_client()
        resp = client.get(
            "/api/auth/google/callback",
            query_string={
                "error": "</script><script>alert(1)</script>",
                "error_description": "boom&</script>",
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        closers = [m.start() for m in re.finditer(r"</script>", body, flags=re.IGNORECASE)]
        self.assertEqual(len(closers), 1)
        self.assertIn("\\u003c/script\\u003e", body)


@unittest.skipUnless(_HAS_FLASK, "stitch-bridge extra not installed")
class OAuthRefreshReuseTests(unittest.TestCase):
    def test_reauth_reuses_stored_refresh_when_google_omits_it(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "stitch_auth.db"
            key_path = Path(td) / ".google_fernet_key"
            with patch.dict(
                os.environ,
                {
                    "STITCH_AUTH_DB": str(db_path),
                    "STITCH_GOOGLE_FERNET_KEY": "test-fernet-key-for-oauth-reuse",
                },
            ):
                import stitch_auth.store as store

                importlib.reload(store)
                # Avoid home-dir key side effects when env key is used; keep path clean.
                _ = key_path
                store.google_account_upsert(
                    "user@example.com",
                    "sub-1",
                    "stored-refresh-token",
                    None,
                )
                app = flask.Flask(__name__)
                register_stitch_auth_routes(app)
                client = app.test_client()
                store.oauth_pending_save(
                    "state-abc",
                    "verifier",
                    "http://localhost:1420",
                    None,
                )
                with (
                    patch(
                        "stitch_auth.flask_routes.google_client.exchange_code",
                        return_value={"access_token": "access-only"},
                    ),
                    patch(
                        "stitch_auth.flask_routes.google_client.userinfo_from_token_response",
                        return_value={"email": "user@example.com", "sub": "sub-1", "picture": None},
                    ),
                ):
                    resp = client.get(
                        "/api/auth/google/callback",
                        query_string={"state": "state-abc", "code": "code-1"},
                    )
                self.assertEqual(resp.status_code, 200)
                body = resp.get_data(as_text=True)
                self.assertIn("stitch_oauth_session=", body)
                self.assertNotIn("no_refresh_token", body)
                row = store.google_account_by_email("user@example.com")
                assert row is not None
                self.assertEqual(store.decrypt_refresh(row), "stored-refresh-token")
                store._reset_connection_for_tests()

    def test_first_login_still_requires_refresh_token(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "stitch_auth.db"
            with patch.dict(
                os.environ,
                {
                    "STITCH_AUTH_DB": str(db_path),
                    "STITCH_GOOGLE_FERNET_KEY": "test-fernet-key-for-oauth-reuse",
                },
            ):
                import stitch_auth.store as store

                importlib.reload(store)
                app = flask.Flask(__name__)
                register_stitch_auth_routes(app)
                client = app.test_client()
                store.oauth_pending_save(
                    "state-new",
                    "verifier",
                    "http://localhost:1420",
                    None,
                )
                with (
                    patch(
                        "stitch_auth.flask_routes.google_client.exchange_code",
                        return_value={"access_token": "access-only"},
                    ),
                    patch(
                        "stitch_auth.flask_routes.google_client.userinfo_from_token_response",
                        return_value={"email": "new@example.com", "sub": "sub-new", "picture": None},
                    ),
                ):
                    resp = client.get(
                        "/api/auth/google/callback",
                        query_string={"state": "state-new", "code": "code-2"},
                    )
                body = resp.get_data(as_text=True)
                self.assertIn("no_refresh_token", body)
                self.assertIsNone(store.google_account_by_email("new@example.com"))
                store._reset_connection_for_tests()


if __name__ == "__main__":
    unittest.main()
