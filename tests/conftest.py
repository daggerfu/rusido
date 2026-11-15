"""Общие фикстуры: пакет устанавливается через PYTHONPATH=src (см. AGENTS.md)."""

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rusido import RusidoAnalyzer, RusidoTranslator, RusidoValidator  # noqa: E402


@pytest.fixture
def translator() -> RusidoTranslator:
    return RusidoTranslator()


@pytest.fixture
def heuristic_translator() -> RusidoTranslator:
    """Переводчик без NLP — на собственных эвристиках MVP."""
    return RusidoTranslator(use_nlp=False)


@pytest.fixture
def validator() -> RusidoValidator:
    return RusidoValidator()


@pytest.fixture
def analyzer() -> RusidoAnalyzer:
    return RusidoAnalyzer()
