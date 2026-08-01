import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nami_build.agent_runner import AgentRunResult, build_prompt, ensure_branch, git_branch_name
from nami_build.queue import BuildQueue, JobStatus


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True, capture_output=True)
    (root / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)


class EnsureBranchTests(unittest.TestCase):
    def test_dirty_working_tree_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git_repo(root)
            (root / "wip.txt").write_text("uncommitted\n", encoding="utf-8")

            ok, msg = ensure_branch(root, "nami/build-deadbeef")

            self.assertFalse(ok)
            self.assertIn("dirty", msg.lower())
            current = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            # Must not have switched/created the job branch while dirty.
            self.assertNotEqual(current, "nami/build-deadbeef")

    def test_clean_tree_creates_job_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git_repo(root)

            ok, msg = ensure_branch(root, "nami/build-cafebabe")

            self.assertTrue(ok)
            self.assertIn("nami/build-cafebabe", msg)
            current = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(current, "nami/build-cafebabe")

    def test_process_job_skips_agent_when_tree_dirty(self):
        from nami_build.worker import process_job

        with tempfile.TemporaryDirectory() as tmp:
            q = BuildQueue(root=Path(tmp) / "queue")
            job = q.enqueue("must not run on dirty tree")
            repo = Path(tmp) / "repo"
            repo.mkdir()
            _init_git_repo(repo)
            (repo / "wip.txt").write_text("local edits\n", encoding="utf-8")

            with (
                patch("nami_build.worker.resolve_repo_path", return_value=repo),
                patch(
                    "nami_build.worker.run_cursor_agent",
                    return_value=AgentRunResult(ok=True, summary="should not run"),
                ) as mock_agent,
            ):
                finished = process_job(q, job)

            self.assertEqual(finished.status, JobStatus.FAILED)
            self.assertIn("dirty", finished.error.lower())
            mock_agent.assert_not_called()
            self.assertEqual((repo / "wip.txt").read_text(encoding="utf-8"), "local edits\n")


class BuildQueueTests(unittest.TestCase):
    def test_enqueue_and_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = BuildQueue(root=Path(tmp))
            job = q.enqueue("Add health route to dev_dashboard", source="test")
            self.assertEqual(len(job.id), 12)
            self.assertEqual(job.status, JobStatus.PENDING)

            loaded = q.get(job.id)
            assert loaded is not None
            self.assertEqual(loaded.task, job.task)

            pending_path = Path(tmp) / "pending" / f"{job.id}.json"
            self.assertTrue(pending_path.is_file())

    def test_move_to_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = BuildQueue(root=Path(tmp))
            job = q.enqueue("test task")
            job.result_summary = "done"
            q.move(job, JobStatus.COMPLETED)
            finished = q.get(job.id)
            assert finished is not None
            self.assertEqual(finished.status, JobStatus.COMPLETED)

    def test_list_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = BuildQueue(root=Path(tmp))
            q.enqueue("one")
            q.enqueue("two")
            jobs = q.list_recent(limit=5)
            self.assertEqual(len(jobs), 2)


class BuildPromptTests(unittest.TestCase):
    def test_prompt_includes_task(self):
        text = build_prompt("Fix pytest in nami_build", turn_cap=5)
        self.assertIn("Fix pytest in nami_build", text)
        self.assertIn("Turn cap: 5", text)

    def test_branch_name(self):
        self.assertTrue(git_branch_name("abcd1234efgh").startswith("nami/build-"))


class BuildHttpTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.queue_root = Path(self._tmpdir.name)

    @patch.dict("os.environ", {"NAMI_BUILD_TOKEN": "test-secret"}, clear=False)
    def test_enqueue_requires_auth(self):
        from nami_build.http import create_app

        with patch("nami_build.http.BuildQueue", return_value=BuildQueue(root=self.queue_root)):
            app = create_app(start_worker=False)
            client = app.test_client()
            resp = client.post("/api/build/enqueue", json={"task": "hello"})
            self.assertEqual(resp.status_code, 401)

    @patch("nami_build.http._auth_ok", return_value=True)
    def test_enqueue_creates_job(self, _mock_auth):
        from nami_build.http import create_app

        q = BuildQueue(root=self.queue_root)
        with patch("nami_build.http.BuildQueue", return_value=q):
            app = create_app(start_worker=False)
            client = app.test_client()
            resp = client.post(
                "/api/build/enqueue",
                json={"task": "Add route", "source": "telegram"},
                headers={"Authorization": "Bearer test-secret"},
            )
            self.assertEqual(resp.status_code, 201)
            data = resp.get_json()
            self.assertTrue(data["ok"])
            self.assertEqual(data["job"]["task"], "Add route")
            self.assertEqual(len(q.pending_jobs()), 1)


if __name__ == "__main__":
    unittest.main()
