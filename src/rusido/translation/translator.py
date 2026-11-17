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
    ALLO_IMPERATIVE, ALLO_INFINITIVE, ALLO_PAST, ALLO_PRESENT,
    POS_ADJ, POS_NOUN, POS_NUM, POS_PRON, POS_VERB, Lexicon,
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
# Закрытый набор служебных слов с уникальными формами (Rusido.md, 2.2):
# нормализацией не выводятся, фиксируются словарём.
RU_TO_LEMMA_OVERRIDES: dict[str, str] = {
    "что": "што",
    "чтобы": "штоби",
    "который": "кторий",
    "ещё": "ешо",
    # Неправильные русские формы глагола «идти» (Rusido.md, 7.1.1, D-015).
    # Без pymorphy3 эвристика видит только лемму, поэтому форма тоже
    # отображается на словарную запись с алломорфами.
    "иду": "идти",
    "идеш": "идти",
    "идёт": "идти",
    "идет": "идти",
    "идете": "идти",
    "идут": "идти",
    "идём": "идти",
}

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
                 use_nlp: bool = True,
                 grammar: "GrammarProfile | None" = None):
        self.lexicon = lexicon or Lexicon()
        self.grammar = grammar
        self.grammar_version = grammar.version if grammar else grammar_version
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
        words = [p for p in parts if p and _WORD_RE.fullmatch(p)]
        total = hits = 0
        word_index = 0
        out = []
        for part in parts:
            if not part or not _WORD_RE.fullmatch(part):
                out.append(part)
                continue
            total += 1
            previous = tuple(w.lower() for w in
                             words[max(0, word_index - 2):word_index])
            following = tuple(w.lower() for w in
                              words[word_index + 1:word_index + 3])
            word_out = self._translate_word(part, warnings, previous, following)
            if word_out is not None:
                hits += 1
                out.append(word_out)
            else:
                warnings.append(f"неизвестное слово: {part}")
                out.append(normalize_word(part))
            word_index += 1
        return "".join(out), (total, hits)

    def _translate_word(self, raw: str, warnings: list[str],
                        previous: tuple[str, ...] = (),
                        following: tuple[str, ...] = ()) -> str | None:
        """Вернуть форму Русидо либо None, если слово неизвестно."""
        word = raw.lower()
        capitalized = raw[0].isupper()
        # Контекст слева задаёт предпочтительную гипотезу pymorphy3 (D-024):
        # иначе «книги» разбираются как род. ед. независимо от предложения.
        analysis = self._nlp.analyze(
            word,
            accept_lemma=lambda lemma: self.lexicon.has(normalize_word(lemma)),
            prefer_case=_preferred_ru_case(previous, self.lexicon),
        ) if self._nlp else None

        lemma = RU_TO_LEMMA_OVERRIDES.get(word, normalize_word(word))
        entry = self.lexicon.lookup(lemma)
        if entry is None and analysis is not None:
            # NLP даёт нормальную форму: читаю → читать (lemma из pymorphy3).
            entry = self.lexicon.lookup(normalize_word(analysis.lemma))
        if entry is None:
            return None

        if entry.pos == POS_ADJ:
            return _cap(adjectives.build_adjective(entry.stem, self.grammar),
                        capitalized)

        if entry.pos == POS_NOUN:
            # Управление Rusido (§8.6) отличается от русского: «у книги» —
            # дательный, хотя pymorphy3 даёт родительный. Предлог задаёт
            # падеж напрямую; «в/на» остаются на усмотрение гипотезы NLP.
            prep_case = _preposition_rusido_case(previous)
            if prep_case is not None:
                case = prep_case
            elif previous and previous[-1] in _GENITIVE_PREDICATES:
                case = nouns.GENITIVE
            elif previous and previous[-1] in _FUTURE_COPULAS:
                # §7.4: русский косвенный падеж именного сказуемого
                # («студентом», «красивым») не переносится в Русидо.
                case = nouns.NOMINATIVE
            elif analysis and analysis.case:
                case = analysis.case
            else:
                case = _guess_ru_case(raw, word, previous, self.lexicon)
            number = analysis.number if analysis and analysis.number \
                else _guess_ru_number(word, entry.pos)
            form = nouns.inflect_noun(entry.stem, number, case, entry.stem_type,
                                      grammar=self.grammar)
            return _cap(form, capitalized)

        if entry.pos == POS_VERB:
            return _cap(self._verb_form(entry, word, analysis, following),
                        capitalized)

        # Личные местоимения после дательных предлогов принимают косвенную
        # форму (Rusido.md, 5.2 и 8.6): «у меня» → «у мне», «к тебе» → «к тебе».
        if entry.pos == POS_PRON and entry.meta.get("case") == "nom":
            oblique = _governed_oblique(entry, previous)
            if oblique is not None:
                return _cap(oblique, capitalized)

        # Местоимения, числительные, служебные — инвариантные формы.
        return _cap(entry.lemma if entry.source_form is None else entry.source_form,
                    capitalized)

    def _verb_form(self, entry, ru_word: str,
                   analysis: RussianAnalysis | None = None,
                   following: tuple[str, ...] = ()) -> str:
        """Выбор формы глагола: сначала признаки NLP, затем эвристики MVP."""
        # Экзистенциальный предикатор `ест` неизменяем (Rusido.md §8.3):
        # pymorphy3 видит в нём форму «быть» и порождает «естет».
        if entry.meta.get("invariant"):
            return entry.source_form or entry.lemma

        stem_type = entry.stem_type
        # Инфинитивная основа может отличаться от основной (Rusido.md, 7.1.1):
        # ити → и- (инфинитив), ид- (остальные формы).
        inf = entry.source_form or verbs.infinitive(
            entry.stem_for(ALLO_INFINITIVE))

        # Признаки из pymorphy3 (если доступны) — точнее эвристик.
        # Повелительное проверяем вне блока tense: pymorphy3 не ставит ему время.
        if analysis is not None and analysis.mood == "imperative":
            return verbs.imperative(
                entry.stem_for(ALLO_IMPERATIVE),
                plural=analysis.number == "plural", stem_type=stem_type)

        if analysis is not None and analysis.tense:
            if analysis.tense == "past" and analysis.number:
                return verbs.conjugate_past(entry.stem_for(ALLO_PAST),
                                            analysis.number,
                                            stem_type=stem_type)
            if analysis.tense == "future" and not ru_word.startswith("буд"):
                return verbs.conjugate_future(
                    analysis.person or 1, analysis.number or "singular", inf)
            if analysis.tense == "present" and analysis.person and analysis.number:
                return verbs.conjugate_present(
                    entry.stem_for(ALLO_PRESENT), analysis.person,
                    analysis.number, stem_type, grammar=self.grammar)

        # Прошедшее время: читал/читали, писал...
        if re.search(r"([аясь]|или)$", ru_word) and len(ru_word) > 3 \
                and not ru_word.endswith("ть"):
            number = "plural" if ru_word.endswith("и") else "singular"
            return _past_with_prefix(ru_word, entry.stem_for(ALLO_PAST),
                                     number, stem_type)

        # Инфинитив: читать, писать...
        if ru_word.endswith("ть") or ru_word.endswith("ти"):
            return inf

        # Будущее (Rusido.md §7.4, D-025): личная форма `будти` самостоятельна.
        # Инфинитив основного глагола — отдельное слово, а не часть этой формы:
        # будет читать → будет читати, но будет студент → будет студент.
        if ru_word.startswith("буд"):
            person, number = _future_person_number(ru_word)
            return verbs.future_auxiliary(person, number)

        # Повелительное: читайте, читай, пиши...
        if _looks_imperative(ru_word):
            plural = ru_word.endswith("ите") or ru_word.endswith("айте") \
                or ru_word.endswith("йте")
            return verbs.imperative(entry.stem_for(ALLO_IMPERATIVE),
                                    plural=plural, stem_type=stem_type)

        # Настоящее время: лицо по русскому окончанию
        person, number = _present_person_number(ru_word)
        return verbs.conjugate_present(entry.stem_for(ALLO_PRESENT),
                                       person, number, stem_type)


def _cap(form: str, capitalize: bool) -> str:
    return (form[0].upper() + form[1:]) if capitalize and form else form


# Управление предлогов по Rusido.md, 8.6 (см. также D-009).
_GENITIVE_PREPOSITIONS = {"из", "от", "без", "для", "од", "до"}
_DATIVE_PREPOSITIONS = {"у", "к", "ко", "с", "о", "об", "под"}
_COPULAS = {"ест", "есть", "был", "была", "было", "были"}
# Личные формы `будти` в связочной функции (Rusido.md §7.4, D-025):
# следующая именная часть сказуемого стоит в именительном падеже.
_FUTURE_COPULAS = {"буду", "будеш", "будет", "будем", "будете", "будут"}
# После вспомогательного будущего существительное остаётся в именительном
# (D-003): «будет книга», а не объект «будет книгу».
_FUTURE_AUXILIARIES = {"буду", "будеш", "будет", "будем", "будете", "будут"}
# Предикат отсутствия «нет» управляет родительным (Rusido.md, 8.4):
# «У мне нет книго».
_GENITIVE_PREDICATES = {"нет"}

# Предлоги с неоднозначным русским управлением: статика (loct → дат. п.)
# или направление (accs → вин. п.). Гипотезу выбирает pymorphy3 по форме
# существительного, а не по самому предлогу (Rusido.md §8.6).
_AMBIGUOUS_PREPOSITIONS = {"в", "на"}

def _governed_oblique(entry, previous: tuple[str, ...]) -> str | None:
    """Косвенная форма личного местоимения под управлением предлога (§5.2, §8.6).

    Русский «у меня» строится родительным, но в Русидо «у» требует
    дательный: «у мне». Поэтому именительное местоимение после дательного
    предлога заменяется на словарную косвенную форму.
    """
    if not previous or previous[-1] not in _DATIVE_PREPOSITIONS:
        return None
    person, number = entry.meta.get("person"), entry.meta.get("number")
    if person is None or number is None:
        return None
    return numerals.PERSONAL_OBLIQUE.get((person, number))


# Падеж Русидо → русская граммема для `prefer_case` (README.md §13).
_RUSIDO_CASE_TO_GRAMMEME = {
    nouns.NOMINATIVE: "nomn",
    nouns.ACCUSATIVE: "accs",
    nouns.GENITIVE: "gent",
    nouns.DATIVE: "datv",
}


def _preferred_ru_case(previous: tuple[str, ...],
                       lexicon: Lexicon) -> str | None:
    """Контекстная гипотеза русского падежа для выбора разбора pymorphy3.

    Приоритет: управление предлога → объект после глагола (SVO) →
    подлежащее. Для «в/на» гипотезу оставляем pymorphy3: только форма
    существительного решает, статика это или направление (D-024).
    """
    if not previous:
        return _RUSIDO_CASE_TO_GRAMMEME[nouns.NOMINATIVE]
    prev = previous[-1]
    if prev in _GENITIVE_PREPOSITIONS or prev in _GENITIVE_PREDICATES:
        return _RUSIDO_CASE_TO_GRAMMEME[nouns.GENITIVE]
    if prev in _DATIVE_PREPOSITIONS:
        return _RUSIDO_CASE_TO_GRAMMEME[nouns.DATIVE]
    if prev in _AMBIGUOUS_PREPOSITIONS:
        return None
    if _likely_object("", previous, lexicon):
        return _RUSIDO_CASE_TO_GRAMMEME[nouns.ACCUSATIVE]
    return _RUSIDO_CASE_TO_GRAMMEME[nouns.NOMINATIVE]


def _preposition_rusido_case(previous: tuple[str, ...]) -> str | None:
    """Падеж Русидо по управлению предлога (Rusido.md §8.6, D-009, D-013)."""
    if not previous:
        return None
    prev = previous[-1]
    if prev in _GENITIVE_PREPOSITIONS:
        return nouns.GENITIVE
    if prev in _DATIVE_PREPOSITIONS:
        return nouns.DATIVE
    return None


def _guess_ru_case(raw: str, word: str, previous: tuple[str, ...] = (),
                   lexicon: Lexicon | None = None) -> str:
    """Эвристика падежа: русское окончание + минимальный контекст слева.

    Полный разбор делает pymorphy3; здесь различаются только те случаи,
    которые выводятся из окончания и предыдущего слова (README.md, 3.1).
    """
    if previous:
        prep = previous[-1]
        if prep in _GENITIVE_PREPOSITIONS:
            return nouns.GENITIVE
        if prep in _DATIVE_PREPOSITIONS:
            return nouns.DATIVE

    if word.endswith(("а", "я")):
        # Раньше здесь безусловно брался родительный; по SVO слово после
        # глагола — объект, иначе именительный (README.md, 1 и 3.1).
        return nouns.ACCUSATIVE if _likely_object(word, previous, lexicon) \
            else nouns.NOMINATIVE
    if word.endswith(("у", "ю")):
        return nouns.ACCUSATIVE
    if word.endswith("е"):
        return nouns.DATIVE
    if word.endswith(("ом", "ем", "ями", "ами")):
        # Творительного падежа в Русидо нет: он передаётся дательным (D-013).
        return nouns.DATIVE
    if word.endswith(("ов", "ев", "ей")):
        return nouns.GENITIVE
    return nouns.NOMINATIVE


def _likely_object(word: str, previous: tuple[str, ...] = (),
                   lexicon: Lexicon | None = None) -> bool:
    """Признак объекта по позиции после глагола (базовый порядок SVO)."""
    if not previous:
        return False
    prev = previous[-1]
    if prev in _GENITIVE_PREPOSITIONS or prev in _DATIVE_PREPOSITIONS \
            or prev in _COPULAS or prev in _FUTURE_AUXILIARIES:
        return False
    if lexicon is not None:
        entry = lexicon.lookup(normalize_word(prev))
        if entry is not None and entry.pos == POS_VERB:
            return True
    # Fallback для глаголов, которых нет в лексиконе: русские личные окончания.
    return bool(re.search(r"(ешь|ишь|ет|ит|ем|им|ете|ите|ут|ют|ат|ят|л|ла|ли|у|ю)$",
                          prev))


# Окончания, которые выглядят как -и/-ы, но не относятся к существительным:
# прошедшее и повелительное глаголов, прилагательные и местоимения.
_NON_NOUN_PLURAL_ENDINGS = ("ли", "йте", "ите", "ые", "ие", "ыми", "ими")


def _guess_ru_number(word: str, pos: str = POS_NOUN) -> str:
    """Число по русскому окончанию; применяется только к существительным.

    Без pymorphy3 надёжно различаются лишь `ы/и` у nouns; `-ов/-ев` — это
    обычно родительный падеж, а `-а/-я` может быть как ед., так и мн. ч.,
    поэтому такие слова остаются единственным числом (README.md, 3.1).
    """
    if pos != POS_NOUN or word in ("он", "она", "оно", "они"):
        return nouns.SINGULAR
    if word.endswith(_NON_NOUN_PLURAL_ENDINGS):
        return nouns.SINGULAR
    if word.endswith(("ы", "и")):
        return nouns.PLURAL
    return nouns.SINGULAR


def _past_with_prefix(ru_word: str, rusido_stem: str, number: str,
                      stem_type: str) -> str:
    """Прошедшее время: та же основа Русидо + -л/-ли; приставка сохраняется."""
    prefix = ""
    m = re.match(r"^([ввызадоперепроразс][^а-я]*?-|^при|^от|^про|^вы|^за|^до|^пере|^раз)",
                 ru_word)
    if m and m.group(0) != rusido_stem[: len(m.group(0))]:
        prefix = normalize_word(m.group(0))
    from rusido.lexicon.dictionary import VERB_CONSONANT  # noqa: PLC0415
    if stem_type == VERB_CONSONANT:
        rusido_stem = rusido_stem + "е"   # ид + е + л = идел (Rusido.md, 7.3)
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
        # «еш»/«иш» — нормализованные русские «ешь»/«ишь» (ё→е, ъ→ь),
        # а также канонические окончания Русидо present 2sg.
        (("ешь", "ишь", "еш", "иш"), (2, "singular")),
        (("ет", "ёт", "ит"), (3, "singular")),
    ]
    for suffixes, value in table:
        if ru_word.endswith(suffixes):
            return value
    return (1, "singular")
