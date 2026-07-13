from nami_corpus.sync import OUT, sync_corpus


def test_sync_corpus_creates_files():
    stats = sync_corpus()
    assert stats["missing"] == 0
    assert stats["copied"] + stats["skipped"] >= 10


def test_sync_corpus_tracks_agentskills_layout():
    stats = sync_corpus()

    assert stats["missing"] == 0

    assert (OUT / "hermes-nami__skills__brief__SKILL.md").is_file()
    assert (OUT / "hermes-nami__skills__loop-checker__SKILL.md").is_file()
