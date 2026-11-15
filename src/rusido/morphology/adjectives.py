"""Морфология прилагательного (Rusido.md, раздел 4; README.md, 4.3).

ОСНОВА + -ий; прилагательное не изменяется по роду, числу и падежу
и всегда стоит перед существительным.

Степени сравнения аналитические: более X / самий X.
"""

from __future__ import annotations

ADJECTIVE_SUFFIX = "ий"


def build_adjective(stem: str, grammar: "GrammarProfile | None" = None) -> str:
    suffix = grammar.adjective_suffix if grammar is not None else ADJECTIVE_SUFFIX
    return stem + suffix


def comparative(stem_or_form: str) -> str:
    return "более " + stem_or_form


def superlative(stem_or_form: str) -> str:
    return "самий " + stem_or_form
