"""Regression tests for shared RAG lazy-init (no Ollama / llama_index required)."""
from __future__ import annotations

import asyncio
import importlib
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FailingThenSuccessfulWorkflow:
    instances: list["FailingThenSuccessfulWorkflow"] = []

    def __init__(self, model_name: str = "llama3.2") -> None:
        self.model_name = model_name
        self.ready = False
        self.ingested_dirs: list[str] = []
        FailingThenSuccessfulWorkflow.instances.append(self)

    async def ingest_documents(self, directory: str) -> None:
        self.ingested_dirs.append(directory)
        if len(FailingThenSuccessfulWorkflow.instances) == 1:
            raise RuntimeError("temporary ingest failure")
        self.ready = True


class RecordingWorkflow:
    ingested_dirs: list[str] = []

    def __init__(self, model_name: str = "llama3.2") -> None:
        self.model_name = model_name

    async def ingest_documents(self, directory: str) -> None:
        RecordingWorkflow.ingested_dirs.append(directory)


class RagRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_modules = {
            "rag": sys.modules.get("rag"),
            "rag_runtime": sys.modules.get("rag_runtime"),
        }
        FailingThenSuccessfulWorkflow.instances.clear()
        RecordingWorkflow.ingested_dirs.clear()

    def tearDown(self) -> None:
        for name, module in self._previous_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def _import_runtime_with_stub(self, workflow_cls: type):
        rag_stub = types.ModuleType("rag")
        rag_stub.RAGWorkflow = workflow_cls
        sys.modules["rag"] = rag_stub
        sys.modules.pop("rag_runtime", None)
        return importlib.import_module("rag_runtime")

    def test_failed_ingest_does_not_poison_future_rag_queries(self) -> None:
        rag_runtime = self._import_runtime_with_stub(FailingThenSuccessfulWorkflow)

        with self.assertRaisesRegex(RuntimeError, "temporary ingest failure"):
            asyncio.run(rag_runtime.ensure_rag_ready())

        self.assertIsNone(rag_runtime._rag_workflow)

        workflow = asyncio.run(rag_runtime.ensure_rag_ready())

        self.assertIs(workflow, FailingThenSuccessfulWorkflow.instances[1])
        self.assertTrue(workflow.ready)
        self.assertIs(rag_runtime._rag_workflow, workflow)

    def test_default_data_dir_is_independent_of_cwd(self) -> None:
        rag_runtime = self._import_runtime_with_stub(RecordingWorkflow)
        previous_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            try:
                with patch.dict(os.environ, {}, clear=False):
                    os.environ.pop("RAG_DATA_DIR", None)
                    workflow = asyncio.run(rag_runtime.ensure_rag_ready())
            finally:
                os.chdir(previous_cwd)

        expected = Path(rag_runtime.__file__).resolve().parent / "data"
        self.assertIsInstance(workflow, RecordingWorkflow)
        self.assertEqual(RecordingWorkflow.ingested_dirs, [str(expected)])

    def test_relative_rag_data_dir_env_resolves_against_repo_root(self) -> None:
        rag_runtime = self._import_runtime_with_stub(RecordingWorkflow)
        previous_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            try:
                with patch.dict(os.environ, {"RAG_DATA_DIR": "data/custom-corpus"}):
                    asyncio.run(rag_runtime.ensure_rag_ready())
            finally:
                os.chdir(previous_cwd)

        expected = Path(rag_runtime.__file__).resolve().parent / "data" / "custom-corpus"
        self.assertEqual(RecordingWorkflow.ingested_dirs, [str(expected)])


if __name__ == "__main__":
    unittest.main()
