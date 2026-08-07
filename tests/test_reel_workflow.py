"""Unit tests for reel_workflow (pure heuristics — no whisper/yt-dlp)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import reel_workflow as rw


class SlugTests(unittest.TestCase):
    def test_reels_path(self) -> None:
        self.assertEqual(
            rw.slug_from_url("https://www.instagram.com/reels/DW7lN7sj2ow/"),
            "DW7lN7sj2ow",
        )

    def test_reel_singular(self) -> None:
        self.assertEqual(
            rw.slug_from_url("https://www.instagram.com/reel/DZ5H6F1Rz1S/"),
            "DZ5H6F1Rz1S",
        )

    def test_fallback_slug(self) -> None:
        slug = rw.slug_from_url("https://example.com/video/abc")
        self.assertTrue(slug)

    def test_instagram_backslash_traversal_sanitized(self) -> None:
        """Windows-style `..\\` in a reel id must not survive as path separators."""
        slug = rw.slug_from_url(r"https://www.instagram.com/reel/..\..\evil")
        self.assertEqual(slug, "evil")
        self.assertNotIn("\\", slug)
        self.assertNotIn("/", slug)
        self.assertNotIn("..", slug)

    def test_instagram_percent_encoded_backslash_sanitized(self) -> None:
        slug = rw.slug_from_url("https://www.instagram.com/reel/..%5c..%5cevil")
        self.assertEqual(slug, "evil")
        self.assertNotIn("..", slug)

    def test_sanitize_slug_strips_separators(self) -> None:
        self.assertEqual(rw.sanitize_slug(r"..\..\tmp\pwned"), "pwned")
        self.assertEqual(rw.sanitize_slug("../x"), "x")
        self.assertEqual(rw.sanitize_slug(".."), "reel")

    def test_write_workflow_card_stays_in_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            inbox = Path(td)
            out = rw.write_workflow_card(
                inbox_dir=inbox,
                slug=r"..\..\outside",
                source_url="https://www.instagram.com/reel/test/",
                transcript_text="First go to Whisk. Then open Google Flow.",
            )
            self.assertEqual(out.parent.resolve(), inbox.resolve())
            self.assertEqual(out.name, "outside.workflow.md")
            self.assertTrue(out.is_file())


class CleanTranscriptTests(unittest.TestCase):
    def test_whisper_tool_fixes(self) -> None:
        raw = "Go to Easy Gift and use cloud design with Revan your cat MCP."
        cleaned = rw.clean_transcript(raw)
        self.assertIn("ezgif", cleaned)
        self.assertIn("Claude design", cleaned)
        self.assertIn("RevenueCat", cleaned)


class ClassifyTypeTests(unittest.TestCase):
    def test_scroll_reel_is_tutorial(self) -> None:
        text = (
            "First go to Whisk. Then open Google Flow. Next upload to Easy Gift. "
            "Download them as a zip. Paste in your coding tool."
        )
        self.assertEqual(rw.classify_type(rw.clean_transcript(text)), "tutorial")

    def test_luke_reel_is_opinion(self) -> None:
        text = (
            "Nope this is one of the biggest mistakes. Overall his breakdown was okay. "
            "Hot take Codex is better. Trust me I tried."
        )
        self.assertEqual(rw.classify_type(text), "opinion")


class WorkflowCardTests(unittest.TestCase):
    def test_render_includes_sections(self) -> None:
        card = rw.build_workflow_card(
            slug="DW7lN7sj2ow",
            source_url="https://www.instagram.com/reels/DW7lN7sj2ow/",
            transcript_text="First go to Whisk. Then open Google Flow.",
            transcript_rel_path="data/inbox/DW7lN7sj2ow.md",
        )
        md = rw.render_workflow_markdown(card)
        self.assertIn("## Steps", md)
        self.assertIn("## Surface map", md)
        self.assertIn("## MVP slice", md)
        self.assertIn("## Not doing", md)
        self.assertEqual(card.workflow_type, "tutorial")


if __name__ == "__main__":
    unittest.main()
