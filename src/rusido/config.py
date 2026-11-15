"""Настройки проекта (README.md, разделы 7.1 и 10)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RusidoConfig:
    grammar_version: str = "1.0"
    analysis_backend: str = "spacy"
    # Использовать pymorphy3 для разбора русских форм (при отсутствии —
    # автоматический откат на эвристики MVP).
    use_nlp: bool = True
    strict: bool = False
