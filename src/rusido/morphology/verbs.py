"""Морфология глагола (Rusido.md, раздел 7; README.md, 4.2).

    инфинитив:   ОСНОВА + -ти
    настоящее:   -м -ш -т | -ми -те -ни (при согласной основе — соединительная «е»)
    прошедшее:   ед. -л / мн. -ли
    будущее:     личная форма «будти» + инфинитив
    повелительное: согласная основа + -и, гласная + -й (мн. ч.: + -те)
    условное:    би + прошедшее
    отрицание:   не + глагол
"""

from __future__ import annotations

from rusido.exceptions import InvalidFeatureError
from rusido.lexicon.dictionary import VERB_CONSONANT
from rusido.morphology.nouns import is_vowel

PRESENT_SG = ("м", "ш", "т")
PRESENT_PL = ("ми", "те", "ни")

PAST_SINGULAR = "л"
PAST_PLURAL = "ли"

FUTURE_STEM = "буд"
FUTURE_FORMS = {
    (1, S := "sg"): "будем",
    (2, S): "будеш",
    (3, S): "будет",
    (1, P := "pl"): "будеми",
    (2, P): "будете",
    (3, P): "будени",
}
del S, P

CONJUGATION_TABLE = {
    ("present", 1, "singular"): PRESENT_SG[0],
    ("present", 2, "singular"): PRESENT_SG[1],
    ("present", 3, "singular"): PRESENT_SG[2],
    ("present", 1, "plural"): PRESENT_PL[0],
    ("present", 2, "plural"): PRESENT_PL[1],
    ("present", 3, "plural"): PRESENT_PL[2],
}


def infinitive(stem: str) -> str:
    return stem + "ти"


def _attach(stem: str, suffix: str, stem_type: str) -> str:
    """Присоединить окончание; при согласной основе вставить «е» (Rusido.md, 7.2)."""
    if stem_type == VERB_CONSONANT and stem and not is_vowel(stem[-1]):
        return stem + "е" + suffix
    return stem + suffix


def conjugate_present(stem: str, person: int, number: str = "singular",
                      stem_type: str = "vowel_stem",
                      grammar: "GrammarProfile | None" = None) -> str:
    if grammar is None:
        try:
            suffix = CONJUGATION_TABLE[("present", person, number)]
        except KeyError:
            raise InvalidFeatureError(
                f"недопустимая комбинация: лицо={person}, число={number!r}"
            ) from None
        return _attach(stem, suffix, stem_type)
    from rusido.core.grammar import present_suffix
    return _attach(stem, present_suffix(grammar, person, number), stem_type)


def conjugate_past(stem: str, number: str = "singular",
                   grammar: "GrammarProfile | None" = None) -> str:
    if grammar is not None:
        suffix = {"singular": grammar.past_sg,
                  "plural": grammar.past_pl}.get(number)
        if suffix is None:
            raise InvalidFeatureError(f"неизвестное число: {number!r}")
        return stem + suffix
    if number == "singular":
        return stem + PAST_SINGULAR
    if number == "plural":
        return stem + PAST_PLURAL
    raise InvalidFeatureError(f"неизвестное число: {number!r}")


def conjugate_future(person: int, number: str, infinitive_form: str) -> str:
    key = (person, "sg" if number == "singular" else "pl")
    if key not in FUTURE_FORMS:
        raise InvalidFeatureError(f"недопустимая комбинация: лицо={person}, число={number!r}")
    return FUTURE_FORMS[key] + " " + infinitive_form


def imperative(stem: str, plural: bool = False, stem_type: str = "vowel_stem") -> str:
    """Повелительное наклонение (Rusido.md, 7.5).

    Основа на согласный: + и (ид → иди); основа на гласный: + й (чита → читай).
    Множественное число: ед. форма повелительного + те (идите, читайте, делайте).
    """
    if stem_type == VERB_CONSONANT or (stem and not is_vowel(stem[-1])):
        form = stem + "и"
    else:
        form = stem + "й"
    return form + "те" if plural else form


def conditional(stem: str, number: str = "singular") -> str:
    """Условное наклонение: би + прошедшее время (Rusido.md, 7.6)."""
    return "би " + conjugate_past(stem, number)


def negate(form: str) -> str:
    """Отрицание: не + глагол (Rusido.md, 7.7)."""
    return "не " + form
