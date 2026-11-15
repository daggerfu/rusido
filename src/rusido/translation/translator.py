"""Переводчик русский → Русидо (README.md, разделы 3.1, 7.2, 7.6).

MVP-подход: собственный регулярный русско-русидский лексикон и морфология,
без обязательных внешних NLP-моделей (pymorphy3/spacy опциональны в полной
версии). Перевод выполняется построчно и пословно; неизвестные слова
нормализуются орфографически и помечаются предупреждением.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rusido.core.nlp import RussianAnalysis, RussianMorphAnalyzer
from rusido.core.normalizer import normalize_word
from rusido.lexicon.dictionary import (
    POS_ADJ, POS_NOUN, POS_NUM, POS_VERB, Lexicon,
)
from rusido.morphology import adjectives, nouns, numerals, verbs

_RU_CASE_TO_RUSIDO = {
    "имен": nouns.NOMINATIVE,
    "вини": nouns.ACCUSATIVE,
    "роди": nouns.GENITIVE,
    "дати": nouns.DATIVE,
}

# Таблица соответствия: русская лемма → ключ записи лексикона Русидо.
# Соблюдает правила орфографии Русидо (Rusido.md, 2.2): ё→е, ы→и, э→е.
# Лемма «большой» совпадает с лексиконом, отдельный override не требуется:
# основа «болш» хранится в записи лексикона и даёт форму «болший».
RU_TO_LEMMA_OVERRIDES: dict[str, str] = {}

_WORD_RE = re.compile(r"[а-яёьъ]+", re.IGNORECASE)


@dataclass
class TranslationResult:
    source: str
    text: str
    warnings: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    confidence: float = 1.0
    grammar_version: str = "1.0"


class RusidoTranslator:
    def __init__(self, lexicon: Lexicon | None = None, grammar_version: str = "1.0",
                 use_nlp: bool = True):
        self.lexicon = lexicon or Lexicon()
        self.grammar_version = grammar_version
        # NLP-анализатор опционален: без pymorphy3 работают эвристики MVP.
        self._nlp = RussianMorphAnalyzer() if use_nlp else None

    @property
    def nlp_available(self) -> bool:
        return self._nlp is not None and self._nlp.available

    # ---------- публичный API ----------

    def translate(self, text: str) -> TranslationResult:
        warnings: list[str] = []
        out_lines = []
        known_total = 0
        known_hits = 0

        for line in text.splitlines() or [""]:
            translated, stats = self._translate_line(line, warnings)
            known_total += stats[0]
            known_hits += stats[1]
            out_lines.append(translated)

        result_text = "\n".join(out_lines)
        confidence = known_hits / known_total if known_total else 1.0
        return TranslationResult(
            source=text,
            text=result_text,
            warnings=warnings,
            confidence=round(confidence, 3),
            grammar_version=self.grammar_version,
        )

    def translate_batch(self, texts: list[str]) -> list[TranslationResult]:
        return [self.translate(t) for t in texts]

    # ---------- внутренняя логика ----------

    def _translate_line(self, line: str,
                        warnings: list[str]) -> tuple[str, tuple[int, int]]:
        # Сохраняем пунктуацию и пробелы: разбиваем строку на «слова» и «шум».
        parts = re.split(r"([а-яёьъА-ЯЁЬЪ]+)", line)
        total = hits = 0
        out = []
        for part in parts:
            if not part or not _WORD_RE.fullmatch(part):
                out.append(part)
                continue
            total += 1
            word_out = self._translate_word(part, warnings)
            if word_out is not None:
                hits += 1
                out.append(word_out)
            else:
                warnings.append(f"неизвестное слово: {part}")
                out.append(normalize_word(part))
        return "".join(out), (total, hits)

    def _translate_word(self, raw: str, warnings: list[str]) -> str | None:
        """Вернуть форму Русидо либо None, если слово неизвестно."""
        word = raw.lower()
        capitalized = raw[0].isupper()
        analysis = self._nlp.analyze(
            word, accept_lemma=lambda lemma: self.lexicon.has(
                normalize_word(lemma))) if self._nlp else None

        lemma = RU_TO_LEMMA_OVERRIDES.get(word, normalize_word(word))
        entry = self.lexicon.lookup(lemma)
        if entry is None and analysis is not None:
            # NLP даёт нормальную форму: читаю → читать (lemma из pymorphy3).
            entry = self.lexicon.lookup(normalize_word(analysis.lemma))
        if entry is None:
            return None

        if entry.pos == POS_ADJ:
            return _cap(adjectives.build_adjective(entry.stem), capitalized)

        if entry.pos == POS_NOUN:
            case = analysis.case if analysis and analysis.case \
                else _guess_ru_case(raw, word)
            number = analysis.number if analysis and analysis.number \
                else _guess_ru_number(word)
            form = nouns.inflect_noun(entry.stem, number, case, entry.stem_type)
            return _cap(form, capitalized)

        if entry.pos == POS_VERB:
            return _cap(self._verb_form(entry, word, analysis), capitalized)

        # Местоимения, числительные, служебные — инвариантные формы.
        return _cap(entry.lemma if entry.source_form is None else entry.source_form,
                    capitalized)

    def _verb_form(self, entry, ru_word: str,
                   analysis: RussianAnalysis | None = None) -> str:
        """Выбор формы глагола: сначала признаки NLP, затем эвристики MVP."""
        stem, stem_type = entry.stem, entry.stem_type
        inf = entry.source_form or verbs.infinitive(stem)

        # Признаки из pymorphy3 (если доступны) — точнее эвристик.
        if analysis is not None and analysis.tense:
            if analysis.tense == "past" and analysis.number:
                return verbs.conjugate_past(stem, analysis.number)
            if analysis.tense == "future" and not ru_word.startswith("буд"):
                return verbs.conjugate_future(
                    analysis.person or 1, analysis.number or "singular", inf)
            if analysis.mood == "imperative":
                return verbs.imperative(
                    stem, plural=analysis.number == "plural", stem_type=stem_type)
            if analysis.tense == "present" and analysis.person and analysis.number:
                return verbs.conjugate_present(
                    stem, analysis.person, analysis.number, stem_type)

        # Прошедшее время: читал/читали, писал...
        if re.search(r"([аясь]|или)$", ru_word) and len(ru_word) > 3 \
                and not ru_word.endswith("ть"):
            past_stem = _ru_past_stem(ru_word)
            number = "plural" if ru_word.endswith(("и",)) else "singular"
            # основа Русидо берётся из словаря, окончание — из числа
            return verbs.conjugate_past(stem, number) if False else \
                _past_with_prefix(ru_word, stem, number, stem_type)

        # Инфинитив: читать, писать...
        if ru_word.endswith("ть") or ru_word.endswith("ти"):
            return inf

        # Будущее: буду/будешь/будем + инфинитив
        if ru_word.startswith("буд"):
            person, number = _future_person_number(ru_word)
            return verbs.conjugate_future(person, number, inf)

        # Повелительное: читайте, читай, пиши...
        if ru_word.endswith("те") and not ru_word.endswith("ете-те"):
            pass  #handled below by imperative heuristic
        if _looks_imperative(ru_word):
            plural = ru_word.endswith("ите") or ru_word.endswith("айте") \
                or ru_word.endswith("йте")
            return verbs.imperative(stem, plural=plural, stem_type=stem_type)

        # Настоящее время: лицо по русскому окончанию
        person, number = _present_person_number(ru_word)
        return verbs.conjugate_present(stem, person, number, stem_type)


def _cap(form: str, capitalize: bool) -> str:
    return (form[0].upper() + form[1:]) if capitalize and form else form


def _guess_ru_case(raw: str, word: str) -> str:
    """Эвристика падежа по русскому окончанию (для MVP)."""
    if word.endswith(("а", "я")):
        return nouns.ACCUSATIVE if _likely_object(word) else nouns.GENITIVE
    if word.endswith(("у", "ю")):
        return nouns.ACCUSATIVE
    if word.endswith(("е",)):
        return nouns.DATIVE
    if word.endswith(("ом", "ем", "ями", "ами")):
        return nouns.DATIVE  # творительный отображается на дательный (README 13)
    if word.endswith(("ов", "ев", "ей")):
        return nouns.GENITIVE
    return nouns.NOMINATIVE


def _likely_object(word: str) -> bool:
    return False


def _guess_ru_number(word: str) -> str:
    if word.endswith(("ы", "и", "ов", "ев")) and word not in ("он",):
        # грубая оценка: окончание мн. ч. русского
        if word.endswith(("ы", "и")):
            return nouns.PLURAL
    return nouns.SINGULAR


def _ru_past_stem(ru_word: str) -> str:
    m = re.match(r"(.*?)(?:л|ла|ло|ли)$", ru_word)
    return normalize_word(m.group(1)) if m else normalize_word(ru_word)


def _past_with_prefix(ru_word: str, rusido_stem: str, number: str,
                      stem_type: str) -> str:
    """Прошедшее время: та же основа Русидо + -л/-ли; приставка сохраняется."""
    prefix = ""
    m = re.match(r"^([ввызадоперепроразс][^а-я]*?-|^при|^от|^про|^вы|^за|^до|^пере|^раз)",
                 ru_word)
    if m and m.group(0) != rusido_stem[: len(m.group(0))]:
        prefix = normalize_word(m.group(0))
    return prefix + rusido_stem + ("ли" if number == "plural" else "л")


def _future_person_number(ru_word: str) -> tuple[int, str]:
    table = {
        "буду": (1, "singular"), "будешь": (2, "singular"),
        "будет": (3, "singular"), "будем": (1, "plural"),
        "будете": (2, "plural"), "будут": (3, "plural"),
    }
    return table.get(ru_word, (1, "singular"))


def _looks_imperative(ru_word: str) -> bool:
    return bool(re.search(r"(ай|я|ий|ьте|ите)$", ru_word)) and \
        not ru_word.endswith("ить")


def _present_person_number(ru_word: str) -> tuple[int, str]:
    """Лицо и число по русскому настоящему времени (окончания -ю/-у/-ешь/...)."""
    table = [
        (("ем", "им"), (1, "plural")),
        (("ете",), (2, "plural")),
        (("ут", "ют"), (3, "plural")),
        (("у", "ю"), (1, "singular")),
        (("ешь", "ишь"), (2, "singular")),
        (("ет", "ёт", "ит"), (3, "singular")),
    ]
    for suffixes, value in table:
        if ru_word.endswith(suffixes):
            return value
    return (1, "singular")
