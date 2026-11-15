"""Морфология существительного (Rusido.md, раздел 3; README.md, 4.1).

Формула: ROOT + NUMBER + CASE, порядок морфем фиксирован.

    число:  ед. ∅ / мн. -и
    падеж:  им. ∅ / вин. -у / род. -о / дат. -е
"""

from __future__ import annotations

from rusido.exceptions import InvalidFeatureError
from rusido.lexicon.dictionary import STEM_PALATAL

SINGULAR = "singular"
PLURAL = "plural"

NUMBERS = (SINGULAR, PLURAL)
NUMBER_SUFFIXES = {SINGULAR: "", PLURAL: "и"}

NOMINATIVE = "nominative"
ACCUSATIVE = "accusative"
GENITIVE = "genitive"
DATIVE = "dative"

CASES = (NOMINATIVE, ACCUSATIVE, GENITIVE, DATIVE)
CASE_SUFFIXES = {NOMINATIVE: "", ACCUSATIVE: "у", GENITIVE: "о", DATIVE: "е"}

VOWELS = "аеиюояэ"


def is_vowel(ch: str) -> bool:
    return ch in VOWELS


def inflect_noun(stem: str, number: str = SINGULAR, case: str = NOMINATIVE,
                 stem_type: str = "vowel",
                 grammar: "GrammarProfile | None" = None) -> str:
    """Построить словоформу существительного по основе.

    Мягкая основа (типа «двер-ь») теряет «ь» перед гласным аффиксом числа
    или падежа: двер + и → двери (по образцу книг → книги).

    Параметр `grammar` позволяет строить формы по произвольной версии
    грамматики (core/grammar.py); без него используются константы модуля.
    """
    if grammar is None:
        if number not in NUMBERS:
            raise InvalidFeatureError(f"неизвестное число: {number!r}")
        if case not in CASES:
            raise InvalidFeatureError(f"неизвестный падеж: {case!r}")
        number_suf, case_suf = NUMBER_SUFFIXES[number], CASE_SUFFIXES[case]
    else:
        from rusido.core.grammar import case_suffix, number_suffix
        number_suf = number_suffix(grammar, number)
        case_suf = case_suffix(grammar, case)

    base = stem
    if stem_type == STEM_PALATAL and base.endswith("ь"):
        base = base[:-1]

    return base + number_suf + case_suf


def split_number_case(rest: str,
                      grammar: "GrammarProfile | None" = None) -> tuple[str, str] | None:
    """Разделить остаток после основы на (аффикс числа, аффикс падежа)."""
    if grammar is not None:
        plural = grammar.noun_number.get("plural", "и")
        case_suffixes = set(grammar.noun_case.values()) - {""}
        if rest == "":
            return "", ""
        if rest in case_suffixes:
            return "", rest
        if rest == plural:
            return plural, ""
        if rest.startswith(plural) and rest[len(plural):] in case_suffixes:
            return plural, rest[len(plural):]
        return None
    if rest == "":
        return "", ""
    if rest in ("у", "о", "е"):
        return "", rest
    if rest == "и":
        return "и", ""
    if rest.startswith("и") and rest[1:] in ("у", "о", "е"):
        return "и", rest[1:]
    return None


def segment_noun(word: str, stems: list[str],
                 grammar: "GrammarProfile | None" = None) -> tuple[str, str, str] | None:
    """Разобрать словоформу по морфемной схеме ROOT + NUMBER + CASE.

    Валидатор проверяет форму именно по морфемной структуре с опорой на
    словарную основу (README.md, 4.1 и 13.4), а не по простому набору
    окончаний. Возвращает (root, number_suffix, case_suffix) или None.
    """
    candidates = []
    for stem in stems:
        # Обычный вариант: аффиксы стоят сразу после основы (стол → стол-∅-у).
        if word.startswith(stem):
            parsed = split_number_case(word[len(stem):], grammar)
            if parsed is not None:
                candidates.append((stem,) + parsed)
        # Мягкая основа, записанная с «ь» (имень): форма может содержать ь.
        if word.startswith(stem + "ь"):
            parsed = split_number_case(word[len(stem) + 1:], grammar)
            if parsed is not None:
                candidates.append((stem + "ь",) + parsed)
        # Чередование мягкой основы: двер(ь) → двери (ь выпадает перед гласным).
        if stem.endswith("ь") and word.startswith(stem[:-1]):
            rest = word[len(stem) - 1:]
            if rest and is_vowel(rest[0]):
                parsed = split_number_case(rest, grammar)
                if parsed is not None:
                    candidates.append((stem,) + parsed)
    if not candidates:
        return None
    # Самое длинное совпадение с основой — наиболее вероятный разбор.
    return max(candidates, key=lambda c: len(c[0]))


# --- Распознавание форм глагола (для валидатора и анализатора) ---

PRESENT_SUFFIXES = {"м": (1, "singular"), "ш": (2, "singular"), "т": (3, "singular"),
                    "ми": (1, "plural"), "те": (2, "plural"), "ни": (3, "plural")}

PAST_SUFFIXES = {"л": "singular", "ли": "plural"}


def segment_verb(form: str, stems: set[str],
                 consonant_stems: set[str] | None = None,
                 invariant_forms: set[str] | None = None) -> dict | None:
    """Разобрать глагольную форму: инфинитив / настоящее / прошедшее / повелительное.

    Возвращает словарь с ключами stem, mood/tense, person, number либо None.
    Для согласных основ учитывается соединительная гласная «е» (ид → идем, идеш).
    Инвариантные служебные формы (например связка «ест») помечаются no_agreement.
    """
    consonant_stems = consonant_stems or set()
    invariant_forms = invariant_forms or set()

    if form in invariant_forms:
        return {"stem": form, "tense": "present", "no_agreement": True}

    # Инфинитив: основа + ти
    if form.endswith("ти"):
        stem = form[:-2]
        if stem in stems:
            return {"stem": stem, "mood": "infinitive"}

    # Прошедшее: основа + л/ли («читал», «читали»)
    for suf, number in PAST_SUFFIXES.items():
        if form.endswith(suf):
            stem = form[: -len(suf)]
            if stem in stems:
                return {"stem": stem, "tense": "past", "number": number}

    # Настоящее: основа (+е) + личное окончание
    for suf in sorted(PRESENT_SUFFIXES, key=len, reverse=True):
        if form.endswith(suf):
            rest = form[: -len(suf)]
            p, n = PRESENT_SUFFIXES[suf]
            if rest in stems:
                return {"stem": rest, "tense": "present", "person": p, "number": n}
            # Соединительная гласная для основ на согласный: ид + е + м
            if rest.endswith("е") and rest[:-1] in consonant_stems:
                return {"stem": rest[:-1], "tense": "present",
                        "person": p, "number": n, "epenthetic": True}

    # Повелительное: чита+й, ид+и; мн. ч.: +те (читайте, делайте, идите)
    if form.endswith("йте"):
        stem = form[:-3]
        if stem in stems:
            return {"stem": stem, "mood": "imperative", "number": "plural"}
    if form.endswith("й"):
        stem = form[:-1]
        if stem in stems:  # чита → читай, писа → писай
            return {"stem": stem, "mood": "imperative", "number": "singular"}
    if form.endswith("и") and not form.endswith("ти"):
        stem = form[:-1]
        if stem in consonant_stems:  # ид → иди
            if stem.endswith("и") and stem[:-1] in consonant_stems \
                    and form.endswith("ите"):
                # идите: основа ид + и (пов.) + те (мн. ч.)
                return {"stem": stem[:-1], "mood": "imperative", "number": "plural"}
            return {"stem": stem, "mood": "imperative", "number": "singular"}

    return None
