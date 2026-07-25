"""Security regression tests for Stitch bridge OAuth origins and SPA path containment."""

from __future__ import annotations

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
    from flask import Flask

    from bridge.spa import safe_path_under
    from stitch_auth.flask_routes import (
        _normalize_client_origin,
        _resolve_client_origin,
        register_stitch_auth_routes,
    )


@unittest.skipUnless(_HAS_FLASK, "stitch-bridge extra not installed")
class SpaPathContainmentTests(unittest.TestCase):
    def test_rejects_sibling_prefix_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "dist" / "assets"
            sibling = Path(tmp) / "dist" / "assets_secret" / "token.txt"
            base.mkdir(parents=True)
            sibling.parent.mkdir(parents=True)
            sibling.write_text("secret", encoding="utf-8")

            escaped = safe_path_under(str(base), "..", "assets_secret", "token.txt")
            self.assertIsNone(escaped)

    def test_allows_file_under_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "dist" / "assets"
            target = base / "app.js"
            base.mkdir(parents=True)
            target.write_text("ok", encoding="utf-8")

            resolved = safe_path_under(str(base), "app.js")
            self.assertEqual(resolved, str(target.resolve()))

    def test_http_rejects_sibling_spa_root_prefix_escape(self) -> None:
        import bridge.spa as spa_mod
        import stitch_rag_bridge

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            dist = base / "dist"
            dist.mkdir()
            (dist / "index.html").write_text("<html>ok</html>", encoding="utf-8")
            (dist / "assets").mkdir()
            (dist / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")
            evil = base / "dist_evil"
            evil.mkdir()
            (evil / "secret.txt").write_text("outside root", encoding="utf-8")

            spa_mod._spa_extra_routes_registered = False
            stitch_rag_bridge.app.config["STITCH_SPA_ROOT"] = str(dist)
            stitch_rag_bridge.register_stitch_spa_routes()
            client = stitch_rag_bridge.app.test_client()

            ok = client.get("/assets/app.js")
            self.assertEqual(ok.status_code, 200)
            self.assertIn(b"console.log('ok')", ok.data)

            escaped = client.get("/%2e%2e%2Fdist_evil%2Fsecret.txt")
            self.assertEqual(escaped.status_code, 404)
            self.assertNotIn(b"outside root", escaped.data)

            assets_escape = client.get("/assets/..%2F..%2Fdist_evil%2Fsecret.txt")
            self.assertEqual(assets_escape.status_code, 404)
            self.assertNotIn(b"outside root", assets_escape.data)


@unittest.skipUnless(_HAS_FLASK, "stitch-bridge extra not installed")
class OAuthClientOriginTests(unittest.TestCase):
    def test_normalize_rejects_embedded_credentials_and_paths(self) -> None:
        self.assertIsNone(_normalize_client_origin("http://user:pass@localhost:1420"))
        self.assertIsNone(_normalize_client_origin("http://localhost:1420/callback"))
        self.assertEqual(_normalize_client_origin("http://localhost:1420/"), "http://localhost:1420")

    def test_resolve_requires_allowlist(self) -> None:
        allowed = {"http://localhost:1420", "http://127.0.0.1:1420"}
        self.assertEqual(
            _resolve_client_origin("http://localhost:1420", allowed),
            "http://localhost:1420",
        )
        self.assertIsNone(_resolve_client_origin("https://evil.example", allowed))

    def test_oauth_start_rejects_untrusted_client_origin(self) -> None:
        app = Flask(__name__)
        app.config["STITCH_ALLOWED_ORIGINS"] = {"http://localhost:1420", "http://127.0.0.1:1420"}
        register_stitch_auth_routes(app)

        with (
            patch("stitch_auth.flask_routes.google_client.oauth_configured", return_value=True),
            patch("stitch_auth.flask_routes.oauth_pending_save") as save_pending,
        ):
            response = app.test_client().post(
                "/api/auth/google/url",
                json={"client_origin": "https://evil.example"},
            )

        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertEqual(body["error"], "untrusted_client_origin")
        save_pending.assert_not_called()

    def test_oauth_start_accepts_allowlisted_origin(self) -> None:
        app = Flask(__name__)
        app.config["STITCH_ALLOWED_ORIGINS"] = {"http://localhost:1420", "http://127.0.0.1:1420"}
        register_stitch_auth_routes(app)

        with (
            patch("stitch_auth.flask_routes.google_client.oauth_configured", return_value=True),
            patch("stitch_auth.flask_routes.google_client.pkce_pair", return_value=("v", "c")),
            patch(
                "stitch_auth.flask_routes.google_client.build_authorize_url",
                return_value="https://accounts.google.com/o/oauth2/v2/auth?x=1",
            ),
            patch("stitch_auth.flask_routes.oauth_pending_save") as save_pending,
        ):
            response = app.test_client().post(
                "/api/auth/google/url",
                json={"client_origin": "http://localhost:1420"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ok"])
        save_pending.assert_called_once()
        self.assertEqual(save_pending.call_args.args[2], "http://localhost:1420")


if __name__ == "__main__":
    unittest.main()
