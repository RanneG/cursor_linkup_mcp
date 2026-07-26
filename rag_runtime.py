"""
Lazy-init PDF RAG workflow shared by MCP (`server.py`) and Stitch HTTP bridge (`stitch_rag_bridge.py`).

Keeps a single process-global index so MCP and bridge do not duplicate ingest when both run (typical dev: bridge only or MCP only).
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Optional

from rag import RAGWorkflow

_REPO_ROOT = Path(__file__).resolve().parent
_rag_workflow: Optional[RAGWorkflow] = None
_rag_ready_lock = asyncio.Lock()


def resolve_rag_data_dir(raw: str | None = None) -> Path:
    """Resolve the RAG corpus directory relative to this repo, not process CWD."""
    value = (raw if raw is not None else os.getenv("RAG_DATA_DIR", "data")).strip() or "data"
    path = Path(value)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path


async def ensure_rag_ready() -> RAGWorkflow:
    """Build embedding index on first use."""
    global _rag_workflow
    if _rag_workflow is not None:
        return _rag_workflow
    async with _rag_ready_lock:
        if _rag_workflow is None:
            model = os.getenv("RAG_LLM_MODEL", "llama3.2")
            # Build locally and publish only after ingest succeeds so a failed first
            # attempt does not poison every later query until process restart.
            workflow = RAGWorkflow(model_name=model)
            data_dir = resolve_rag_data_dir()
            if not data_dir.is_dir():
                data_dir.mkdir(parents=True, exist_ok=True)
            await workflow.ingest_documents(str(data_dir))
            _rag_workflow = workflow
        return _rag_workflow
