import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nami_build.agent_runner import build_prompt, git_branch_name
from nami_build.queue import BuildQueue, JobStatus


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


class BuildWorkerRecoveryTests(unittest.TestCase):
    def test_fail_stranded_running_marks_jobs_failed(self):
        from nami_build.worker import fail_stranded_running

        with tempfile.TemporaryDirectory() as tmp:
            q = BuildQueue(root=Path(tmp))
            job = q.enqueue("long agent run")
            q.move(job, JobStatus.RUNNING)

            failed = fail_stranded_running(q, "Build job subprocess timed out")

            self.assertEqual(len(failed), 1)
            loaded = q.get(job.id)
            assert loaded is not None
            self.assertEqual(loaded.status, JobStatus.FAILED)
            self.assertIn("timed out", loaded.error)
            self.assertEqual(len(list((Path(tmp) / "running").glob("*.json"))), 0)
            self.assertEqual(len(list((Path(tmp) / "failed").glob("*.json"))), 1)

    def test_process_job_crash_does_not_leave_running(self):
        from nami_build.agent_runner import AgentRunResult
        from nami_build.worker import process_job

        with tempfile.TemporaryDirectory() as tmp:
            q = BuildQueue(root=Path(tmp))
            job = q.enqueue("boom", repo="linkup_mcp")

            with (
                patch("nami_build.worker.resolve_repo_path", return_value=Path(tmp)),
                patch("nami_build.worker.ensure_branch", return_value=(True, "ok")),
                patch(
                    "nami_build.worker.run_cursor_agent",
                    return_value=AgentRunResult(ok=True, summary="changed files"),
                ),
                patch("nami_build.worker.run_pytest", side_effect=RuntimeError("disk full")),
            ):
                finished = process_job(q, job)

            self.assertEqual(finished.status, JobStatus.FAILED)
            self.assertIn("disk full", finished.error)
            self.assertEqual(len(list((Path(tmp) / "running").glob("*.json"))), 0)

    def test_run_pytest_timeout_returns_failure(self):
        from nami_build.agent_runner import run_pytest

        with patch("nami_build.agent_runner.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pytest", timeout=1)):
            ok, out = run_pytest(Path("."), timeout=1)
        self.assertFalse(ok)
        self.assertIn("timed out", out)


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
