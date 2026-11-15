"""Загрузка формальной грамматики из YAML (README.md, §10; §4.6 плана).

Грамматика хранится отдельно от кода (`data/grammar/grammar.yaml`), чтобы
изменение Русидо не требовало переписывания движка. Морфологические модули
пока используют собственные константы; тест `test_grammar_yaml` проверяет,
что YAML и код не расходятся.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_GRAMMAR_PATH = Path("data") / "grammar" / "grammar.yaml"


@dataclass
class GrammarProfile:
    """Формальная грамматика одной версии языка."""

    version: str
    alphabet: str
    forbidden: list[str]
    noun_number: dict[str, str]
    noun_case: dict[str, str]
    verb_infinitive_suffix: str
    present_sg: list[str]
    present_pl: list[str]
    past_sg: str
    past_pl: str
    epenthetic_vowel: str
    adjective_suffix: str
    default_order: str
    raw: dict = field(default_factory=dict, repr=False)


def load_grammar(path: str | Path = DEFAULT_GRAMMAR_PATH) -> GrammarProfile:
    """Прочитать грамматику из YAML-файла."""
    import yaml  # noqa: PLC0415

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    noun = data["noun"]
    verb = data["verb"]
    return GrammarProfile(
        version=str(data["language"]["version"]),
        alphabet=data["orthography"]["alphabet"],
        forbidden=[str(ch) for ch in data["orthography"]["forbidden"]],
        noun_number=dict(noun["number"]),
        noun_case=dict(noun["case"]),
        verb_infinitive_suffix=str(verb["infinitive_suffix"]),
        present_sg=[str(s) for s in verb["present"]["singular"]],
        present_pl=[str(s) for s in verb["present"]["plural"]],
        past_sg=str(verb["past"]["singular"]),
        past_pl=str(verb["past"]["plural"]),
        epenthetic_vowel=str(verb["epenthetic_vowel"]),
        adjective_suffix=str(data["adjective"]["suffix"]),
        default_order=str(data["syntax"]["default_order"]),
        raw=data,
    )
