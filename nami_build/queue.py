"""File-backed build job queue; jobs live as JSON under data/build-queue/."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUEUE_ROOT = ROOT / "data" / "build-queue"

# Prefer advanced/terminal states when a crash left the same job id in two dirs.
_STATUS_PRIORITY = {
    "pending": 1,
    "running": 2,
    "completed": 3,
    "failed": 3,
}


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BuildJob:
    id: str
    task: str
    source: str = "telegram"
    repo: str = "linkup_mcp"
    status: JobStatus = JobStatus.PENDING
    turn_cap: int = 8
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())
    result_summary: str = ""
    branch: str = ""
    error: str = ""
    test_output: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BuildJob:
        status = data.get("status", JobStatus.PENDING.value)
        if isinstance(status, JobStatus):
            status_val = status
        else:
            status_val = JobStatus(str(status))
        return cls(
            id=str(data["id"]),
            task=str(data["task"]),
            source=str(data.get("source", "telegram")),
            repo=str(data.get("repo", "linkup_mcp")),
            status=status_val,
            turn_cap=int(data.get("turn_cap", 8)),
            created_at=str(data.get("created_at", _now())),
            updated_at=str(data.get("updated_at", _now())),
            result_summary=str(data.get("result_summary", "")),
            branch=str(data.get("branch", "")),
            error=str(data.get("error", "")),
            test_output=str(data.get("test_output", "")),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dir_for(status: JobStatus) -> Path:
    return QUEUE_ROOT / status.value


class BuildQueue:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or QUEUE_ROOT
        for status in JobStatus:
            (self.root / status.value).mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str, status: JobStatus) -> Path:
        return self.root / status.value / f"{job_id}.json"

    def _find_path(self, job_id: str) -> Path | None:
        found: list[tuple[int, Path]] = []
        for status in JobStatus:
            path = self._path(job_id, status)
            if path.is_file():
                found.append((_STATUS_PRIORITY[status.value], path))
        if not found:
            return None
        # Highest priority wins (handles write-new-then-delete-old crash windows).
        found.sort(key=lambda item: item[0], reverse=True)
        return found[0][1]

    def enqueue(
        self,
        task: str,
        *,
        source: str = "telegram",
        repo: str = "linkup_mcp",
        turn_cap: int = 8,
    ) -> BuildJob:
        job = BuildJob(
            id=uuid.uuid4().hex[:12],
            task=task.strip(),
            source=source,
            repo=repo,
            turn_cap=max(1, min(turn_cap, 20)),
        )
        self._write(job, JobStatus.PENDING)
        return job

    def get(self, job_id: str) -> BuildJob | None:
        path = self._find_path(job_id)
        if not path:
            return None
        return BuildJob.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_recent(self, limit: int = 10) -> list[BuildJob]:
        jobs: list[BuildJob] = []
        seen: set[str] = set()
        for status in JobStatus:
            for path in sorted(
                (self.root / status.value).glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            ):
                job = BuildJob.from_dict(json.loads(path.read_text(encoding="utf-8")))
                # Deduplicate crash leftovers; prefer the path chosen by _find_path.
                canonical = self._find_path(job.id)
                if canonical is None or canonical != path or job.id in seen:
                    continue
                seen.add(job.id)
                jobs.append(job)
        jobs.sort(key=lambda j: j.updated_at, reverse=True)
        return jobs[:limit]

    def update(self, job: BuildJob) -> None:
        job.updated_at = _now()
        existing = self._find_path(job.id)
        if not existing:
            raise FileNotFoundError(f"Job not found: {job.id}")
        self._write(job, job.status)
        if existing.parent.name != job.status.value:
            existing.unlink(missing_ok=True)
        self._cleanup_stale_copies(job.id, keep=job.status)

    def move(self, job: BuildJob, new_status: JobStatus) -> BuildJob:
        """Move job to a new status directory without a no-file crash window.

        Writes the destination file first, then removes the old status file.
        A crash mid-move may leave a duplicate briefly; _find_path prefers the
        advanced status so the job is never lost.
        """
        old = self._find_path(job.id)
        job.status = new_status
        job.updated_at = _now()
        self._write(job, new_status)
        if old and old.parent.name != new_status.value:
            old.unlink(missing_ok=True)
        self._cleanup_stale_copies(job.id, keep=new_status)
        return job

    def _cleanup_stale_copies(self, job_id: str, *, keep: JobStatus) -> None:
        for status in JobStatus:
            if status == keep:
                continue
            path = self._path(job_id, status)
            if path.is_file():
                path.unlink(missing_ok=True)

    def _write(self, job: BuildJob, status: JobStatus) -> None:
        """Atomically write job JSON (temp file + os.replace)."""
        path = self._path(job.id, status)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(job.to_dict(), indent=2)
        tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(payload, encoding="utf-8")
            os.replace(tmp, path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

    def pending_jobs(self) -> list[BuildJob]:
        pending_dir = self.root / JobStatus.PENDING.value
        jobs: list[BuildJob] = []
        for path in sorted(pending_dir.glob("*.json"), key=lambda x: x.stat().st_mtime):
            job = BuildJob.from_dict(json.loads(path.read_text(encoding="utf-8")))
            # Skip (and scrub) stale pending files left after a crash mid-move.
            advanced = [
                s
                for s in (JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED)
                if self._path(job.id, s).is_file()
            ]
            if advanced:
                path.unlink(missing_ok=True)
                continue
            jobs.append(job)
        return jobs
