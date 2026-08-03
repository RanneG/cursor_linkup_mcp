"""Pure OAuth session finalization helpers (no Flask)."""

from __future__ import annotations

from typing import Any

from stitch_auth.store import session_create, session_load, session_update


def finalize_oauth_session(
    *,
    linking_sid: str | None,
    account_id: int,
    email: str,
) -> tuple[str | None, dict[str, Any] | None]:
    """Resolve the session after Google account upsert.

    Returns ``(session_id, None)`` on success, or ``(None, error_payload)`` when
    a linking flow cannot safely continue (caller should not mint a replacement
    single-account session — that drops previously linked accounts).
    """
    if linking_sid:
        sess = session_load(linking_sid)
        if not sess:
            return None, {
                "ok": False,
                "error": "linking_session_expired",
                "detail": "Sign in again, then retry Add account.",
                "email": email,
            }
        ids = list(sess.get("account_ids") or [])
        if account_id not in ids:
            ids.append(account_id)
        session_update(linking_sid, ids, email)
        return linking_sid, None
    return session_create([account_id], email), None
