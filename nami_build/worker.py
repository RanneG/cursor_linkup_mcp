"""Process pending build jobs on the PC."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from nami_build.agent_runner import (
    ensure_branch,
    git_branch_name,
    git_summary,
    run_cursor_agent,
    run_pytest,
)
from nami_build.queue import BuildJob, BuildQueue, JobStatus

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]

REPO_PATHS: dict[str, Path] = {
    "linkup_mcp": ROOT,
}


def resolve_repo_path(repo: str) -> Path:
    if repo in REPO_PATHS:
        return REPO_PATHS[repo]
    override = Path(repo)
    if override.is_dir():
        return override.resolve()
    raise ValueError(f"Unknown repo: {repo}")


def fail_stranded_running(queue: BuildQueue, reason: str) -> list[BuildJob]:
    """Mark any jobs left in running/ as failed (e.g. after worker subprocess timeout/crash)."""
    running_dir = queue.root / JobStatus.RUNNING.value
    failed: list[BuildJob] = []
    for path in sorted(running_dir.glob("*.json")):
        try:
            job = BuildJob.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
            log.warning("Skipping unreadable running job %s: %s", path.name, exc)
            continue
        job.error = reason
        job.result_summary = reason
        failed.append(queue.move(job, JobStatus.FAILED))
        log.error("Marked stranded build job %s as failed: %s", job.id, reason)
    return failed


def process_job(queue: BuildQueue, job: BuildJob) -> BuildJob:
    queue.move(job, JobStatus.RUNNING)
    try:
        cwd = resolve_repo_path(job.repo)
        branch = git_branch_name(job.id)
        job.branch = branch

        branch_ok, branch_msg = ensure_branch(cwd, branch)
        if not branch_ok:
            job.error = branch_msg
            job.result_summary = f"Branch setup failed: {branch_msg}"
            return queue.move(job, JobStatus.FAILED)

        agent = run_cursor_agent(job.task, cwd, turn_cap=job.turn_cap)
        if not agent.ok:
            job.error = agent.detail or agent.summary
            job.result_summary = agent.summary
            return queue.move(job, JobStatus.FAILED)

        tests_ok, test_out = run_pytest(cwd)
        job.test_output = test_out
        diff = git_summary(cwd)

        job.result_summary = agent.summary
        if diff:
            job.result_summary += f"\n\n{diff}"

        if not tests_ok:
            job.error = "pytest failed after agent run"
            job.result_summary += f"\n\npytest:\n{test_out[-1500:]}"
            return queue.move(job, JobStatus.FAILED)

        job.result_summary = (
            f"Build ready for review on `{branch}`.\n"
            f"{branch_msg}\n\n"
            f"{agent.summary}\n\n"
            f"{diff}"
        ).strip()
        return queue.move(job, JobStatus.COMPLETED)
    except Exception as exc:  # noqa: BLE001 — never leave jobs stuck in running/
        log.exception("Build job %s crashed", job.id)
        job.error = str(exc) or exc.__class__.__name__
        job.result_summary = f"Job failed unexpectedly: {job.error}"
        return queue.move(job, JobStatus.FAILED)


def run_once(queue: BuildQueue | None = None) -> BuildJob | None:
    q = queue or BuildQueue()
    pending = q.pending_jobs()
    if not pending:
        return None
    job = pending[0]
    log.info("Processing build job %s", job.id)
    return process_job(q, job)


class BuildWorker:
    def __init__(self, poll_seconds: float = 15.0) -> None:
        self.poll_seconds = poll_seconds
        self.queue = BuildQueue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="nami-build-worker", daemon=True)
        self._thread.start()
        log.info("Build worker started (poll=%ss)", self.poll_seconds)

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                if self.queue.pending_jobs():
                    # Subprocess avoids WinError 10038 (cursor_sdk + Flask thread on Windows).
                    subprocess.run(
                        [sys.executable, "-m", "nami_build.run_job"],
                        cwd=str(ROOT),
                        env={**os.environ.copy(), "NAMI_BUILD_PYTHON": sys.executable},
                        timeout=int(os.getenv("NAMI_BUILD_JOB_TIMEOUT", "3600")),
                    )
            except subprocess.TimeoutExpired:
                log.error("Build job subprocess timed out")
                fail_stranded_running(self.queue, "Build job subprocess timed out")
            except Exception:
                log.exception("Build worker error")
            self._stop.wait(self.poll_seconds)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    worker = BuildWorker()
    worker.start()
    print("Nami build worker running — Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        worker.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
