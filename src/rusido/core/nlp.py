"""Морфологический анализ русских слов через pymorphy3 (README.md, §7.2, §13).

NLP-библиотека опциональна: если pymorphy3 не установлен, модуль работает
в режиме «нет анализа» и переводчик падает на собственные эвристики MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

# Падежи pymorphy3 → падежи Русидо (morphology/nouns.py).
# Творительный (ablt) и предложный (loct) отображаются на дательный (README.md §13).
RU_CASE_TO_RUSIDO = {
    "nomn": "nominative",
    "accs": "accusative",
    "gent": "genitive",
    "datv": "dative",
    "ablt": "dative",
    "loct": "dative",
}

RU_NUMBER_TO_RUSIDO = {"sing": "singular", "plur": "plural"}

RU_PERSON_TO_INT = {"1per": 1, "2per": 2, "3per": 3}


@dataclass
class RussianAnalysis:
    """Морфологические признаки русского слова (лемма и граммемы pymorphy3)."""

    lemma: str
    pos: str            # NOUN, VERB, INFN, ADJF...
    case: str | None = None      # падеж Русидо
    number: str | None = None    # singular | plural
    person: int | None = None    # 1 | 2 | 3
    tense: str | None = None     # past | present | future
    mood: str | None = None      # indicative | imperative


class RussianMorphAnalyzer:
    """Обёртка над pymorphy3 со статусом доступности."""

    def __init__(self) -> None:
        try:
            import pymorphy3  # noqa: PLC0415
        except ImportError:
            self._morph = None
        else:
            self._morph = pymorphy3.MorphAnalyzer()

    @property
    def available(self) -> bool:
        return self._morph is not None

    def analyze(self, word: str,
                accept_lemma=None) -> RussianAnalysis | None:
        """Разобрать слово; None — если NLP недоступен или слово не разобрано.

        accept_lemma — опциональный предикат на нормальную форму: позволяет
        выбрать тот разбор, чья лемма есть в лексиконе (иначе pymorphy3
        отдаёт первую по частотности гипотезу, напр. причастие «читаемый»).
        """
        if self._morph is None:
            return None
        parses = self._morph.parse(word)
        if not parses:
            return None
        if accept_lemma is not None:
            for p in parses:
                if accept_lemma(p.normal_form):
                    parses = [p] + [q for q in parses if q is not p]
                    break
        p = parses[0]
        tag = p.tag
        pos = tag.POS or ""
        tense = None
        if pos == "VERB":
            tense = {"past": "past", "pres": "present", "futr": "future"}.get(
                tag.tense or "")
        mood = {"indc": "indicative", "impr": "imperative"}.get(tag.mood or "")
        return RussianAnalysis(
            lemma=p.normal_form,
            pos=pos,
            case=RU_CASE_TO_RUSIDO.get(tag.case or ""),
            number=RU_NUMBER_TO_RUSIDO.get(tag.number or ""),
            person=RU_PERSON_TO_INT.get(tag.person or ""),
            tense=tense,
            mood=mood,
        )
