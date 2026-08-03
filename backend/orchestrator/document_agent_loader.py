"""
Loads `document_agent.py` by file path instead of by package import.

The Document Agent lives in a folder called "document Agent" (note the
space), which is not a valid Python package name. Rather than requiring the
repo to be restructured, we load the module dynamically with importlib and
reuse its `DocumentAgent` class and `DocumentAgentConfig` directly, in
process. This also lets us point its vector-store / upload roots at the
orchestrator's shared data directory.
"""
from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from threading import Lock

from config import settings

logger = logging.getLogger("orchestrator.document_agent_loader")

_module = None
_agent = None
_lock = Lock()


def _load_module():
    global _module
    if _module is not None:
        return _module

    module_path = Path(settings.document_agent_path)
    if not module_path.exists():
        raise FileNotFoundError(
            f"Could not find document_agent.py at {module_path}. "
            "Set DOCUMENT_AGENT_PATH to the correct location."
        )

    spec = importlib.util.spec_from_file_location("document_agent_module", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["document_agent_module"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    _module = module
    return module


def get_document_agent():
    """Return a process-wide singleton DocumentAgent instance."""
    global _agent
    if _agent is not None:
        return _agent

    with _lock:
        if _agent is None:
            module = _load_module()
            config = module.DocumentAgentConfig()
            config.VECTOR_STORE_ROOT = Path(settings.vector_store_dir)
            config.UPLOAD_ROOT = Path(settings.upload_dir)
            logger.info("Initializing DocumentAgent (embedding model download may take a moment)...")
            _agent = module.DocumentAgent(config=config)
            logger.info("DocumentAgent ready.")
    return _agent
