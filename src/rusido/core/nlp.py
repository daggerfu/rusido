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

# Русские граммемы падежа, которые переводчик может запросить как
# предпочтительную гипотезу (снятие синкретизма, README.md §13).
RU_CASE_GRAMMEMES = frozenset(RU_CASE_TO_RUSIDO)


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
    transitive: bool | None = None  # True — tran, False — intr, None — нет данных


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

    def analyze(self, word: str, accept_lemma=None, *,
                prefer_case: str | None = None) -> RussianAnalysis | None:
        """Разобрать слово; None — если NLP недоступен или слово не разобрано.

        pymorphy3 возвращает гипотезы в порядке убывания частотной оценки,
        из-за чего синкретичные формы разбираются неверно: «книги» — род. ед.,
        «столы» — вин. мн., «дверь» — вин. ед. (README.md §13). Приоритеты
        выбора (от высокого к низкому):

        1. лемма есть в лексиконе (`accept_lemma`);
        2. падеж совпадает с контекстной гипотезой (`prefer_case`);
        3. оценка pymorphy3.

        `prefer_case` — русская граммема (`RU_CASE_GRAMMEMES`), вычисленная
        переводчиком по контексту: объект после глагола → `accs`, подлежащее
        → `nomn`, предлог → падеж его управления (D-024). Граммема не
        *навязывается*: если подходящей гипотезы нет, остаётся частотная.
        """
        if self._morph is None:
            return None
        parses = self._morph.parse(word)
        if not parses:
            return None
        # Разборы-аббревиатуры (Abbr) отбрасываем: pymorphy3 считает «е»
        # аббревиатурой глагола «быть» и порождает «бует» вместо буквы.
        full = [p for p in parses if "Abbr" not in p.tag]
        if full:
            parses = full
        # Стабильные сортировки сохраняют порядок pymorphy3 внутри группы.
        if accept_lemma is not None:
            parses.sort(key=lambda p: 0 if accept_lemma(p.normal_form) else 1)
        if prefer_case is not None:
            parses.sort(key=lambda p: 0 if (p.tag.case or "") == prefer_case else 1)
        p = parses[0]
        tag = p.tag
        pos = tag.POS or ""
        tense = None
        if pos == "VERB":
            tense = {"past": "past", "pres": "present", "futr": "future"}.get(
                tag.tense or "")
        mood = {"indc": "indicative", "impr": "imperative"}.get(tag.mood or "")
        # Переходность из словаря pymorphy3: tran → True, intr → False (D-026).
        transitive = True if "tran" in tag else False if "intr" in tag else None
        return RussianAnalysis(
            lemma=p.normal_form,
            pos=pos,
            case=RU_CASE_TO_RUSIDO.get(tag.case or ""),
            number=RU_NUMBER_TO_RUSIDO.get(tag.number or ""),
            person=RU_PERSON_TO_INT.get(tag.person or ""),
            tense=tense,
            mood=mood,
            transitive=transitive,
        )

    def is_transitive_verb(self, word: str) -> bool | None:
        """Переходность глагола по словарю pymorphy3: `tran`/`intr`/None.

        None означает, что данных нет или слово глаголом не является.
        Перебираем все гипотезы: у омонимичных форм переходность может
        различаться, и первая по частоте не всегда глагольная.
        """
        if self._morph is None:
            return None
        for p in self._morph.parse(word):
            if p.tag.POS in {"VERB", "INFN"}:
                if "tran" in p.tag:
                    return True
                if "intr" in p.tag:
                    return False
        return None
