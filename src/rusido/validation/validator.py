"""Валидатор Русидо (README.md, разделы 3.2, 9; Rusido.md, разделы 1—10).

Проверяет текст по уровням: орфография → лексика → морфология → синтаксис.
Каждая диагностика имеет стабильный код ошибки (R001—R017).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rusido.core.normalizer import (
    ALPHABET, DOUBLED_CONSONANT, FORBIDDEN_LETTERS, normalize_word,
)
from rusido.lexicon.dictionary import (
    POS_ADJ, POS_ADV, POS_CONJ, POS_NUM, POS_NOUN, POS_PARTICLE, POS_PREP,
    POS_PRON, POS_VERB, Lexicon,
)
from rusido.morphology import adjectives, nouns, verbs

# Личные окончания настоящего времени и их признаки субъекта
PRESENT_PERSON_NUMBER = {
    "м": (1, "sg"), "ш": (2, "sg"), "т": (3, "sg"),
    "ми": (1, "pl"), "те": (2, "pl"), "ни": (3, "pl"),
}
FUTURE_PERSON_NUMBER = {
    "будем": (1, "sg"), "будеш": (2, "sg"), "будет": (3, "sg"),
    "будеми": (1, "pl"), "будете": (2, "pl"), "будени": (3, "pl"),
    # Допустимы также аналитические формы с несклоняемой частью «будти»
    "будти": None,
}
PAST_PLURAL_SUBJECTS = {"ми", "ви", "они"}

_WORD_RE = re.compile(r"[а-яёьъ]+", re.IGNORECASE)


@dataclass
class Diagnostic:
    code: str
    severity: str  # error | warning | info
    message: str
    suggestion: str | None = None
    line: int = 1
    column: int = 0
    start: int = 0
    end: int = 0


@dataclass
class ValidationReport:
    valid: bool
    errors: list[Diagnostic] = field(default_factory=list)
    warnings: list[Diagnostic] = field(default_factory=list)
    sentences: int = 0
    tokens: int = 0

    @property
    def diagnostics(self) -> list[Diagnostic]:
        return self.errors + self.warnings


class RusidoValidator:
    """Главный валидатор Русидо. Работает без внешних NLP-моделей."""

    def __init__(self, lexicon: Lexicon | None = None, strict: bool = False,
                 grammar: "GrammarProfile | None" = None):
        self.lexicon = lexicon or Lexicon()
        self.strict = strict
        self.grammar = grammar

    # ---------- публичный API ----------

    def validate(self, text: str) -> ValidationReport:
        errors: list[Diagnostic] = []
        warnings: list[Diagnostic] = []

        lines = text.splitlines() or [""]
        token_count = 0
        sentence_count = 0

        for lineno, line in enumerate(lines, start=1):
            words = _WORD_RE.findall(line)
            token_count += len(words)
            sentence_count += max(
                len(re.findall(r"[.!?]", line)), 1 if words else 0)

            for match in _WORD_RE.finditer(line):
                word = match.group()
                token_count_local = word
                diags = self._check_word(token_count_local, lineno, match.start())
                for d in diags:
                    (errors if d.severity == "error" else warnings).append(d)

            sent_errors, sent_warnings = self._check_sentence(line, lineno)
            errors.extend(sent_errors)
            warnings.extend(sent_warnings)

        if self.strict and not text.endswith((".", "!", "?")) and text.strip():
            warnings.append(Diagnostic("R017", "warning",
                                       "текст не заканчивается знаком препинания"))

        return ValidationReport(valid=not errors, errors=errors,
                                warnings=warnings, sentences=sentence_count,
                                tokens=token_count)

    def validate_word(self, word: str) -> ValidationReport:
        report = ValidationReport(valid=True)
        for d in self._check_word(word.lower(), 1, 0):
            if d.severity == "error":
                report.errors.append(d)
                report.valid = False
            else:
                report.warnings.append(d)
        return report

    # ---------- уровни проверки слова ----------

    def _check_word(self, word: str, line: int, column: int) -> list[Diagnostic]:
        diags: list[Diagnostic] = []

        # 1. Орфография: запрещённые буквы (R006) — проверяется исходное написание,
        #    исправление даёт нормализованную форму (ёлка → елка, чёрный → черний).
        alphabet = self.grammar.alphabet if self.grammar else ALPHABET
        forbidden = self.grammar.forbidden if self.grammar else FORBIDDEN_LETTERS
        bad = [ch for ch in word.lower() if ch in forbidden]
        if bad:
            fixed = normalize_word(word)
            diags.append(Diagnostic(
                "R006", "error",
                f"запрещённая буква '{bad[0]}'",
                suggestion=fixed, line=line, column=column))
            # Нормализованная форма может быть словарной или разбираться
            # морфологией — проверяем её дальше, не останавливаясь на R006.
            low = fixed.lower()
        else:
            low = word.lower()
        unknown_letters = [ch for ch in low if ch not in alphabet]
        if unknown_letters:
            diags.append(Diagnostic(
                "R018", "error",
                f"символ вне алфавита: '{unknown_letters[0]}'",
                line=line, column=column))
            return diags

        # Удвоенные согласные запрещены (Rusido.md, 2.6) — код R007.
        m = DOUBLED_CONSONANT.search(low)
        if m:
            diags.append(Diagnostic(
                "R007", "error",
                f"удвоенная согласная '{m.group()}'",
                suggestion=normalize_word(word),
                line=line, column=column))
            return diags

        # 2. Лексика: слово известно как лемма или каноническая форма (R005)
        if self.lexicon.has(low) or self.lexicon.lookup_form(low) is not None:
            return diags

        # 3. Морфология: проба разобрать форму по схеме ROOT+NUMBER+CASE и т.п.
        if self._known_noun_form(low) is not None:
            return diags
        if self._known_verb_form(low) is not None:
            return diags
        if low.endswith(adjectives.ADJECTIVE_SUFFIX) and \
                low[: -len(adjectives.ADJECTIVE_SUFFIX)] in self._adj_stems():
            return diags

        diags.append(Diagnostic(
            "R005", "error", f"неизвестное слово '{word}'",
            suggestion=self._suggest(low), line=line, column=column))
        return diags

    # ---------- уровень предложения ----------

    def _check_sentence(self, line: str, lineno: int) -> tuple[list, list]:
        errors, warnings = [], []
        words = [w.lower() for w in _WORD_RE.findall(line)]
        if not words:
            return errors, warnings

        # R001 — согласование подлежащего и сказуемого в настоящем времени.
        # Формы «ест» (связка) и повелительного наклонения не проверяются.
        for i, w in enumerate(words):
            info = self._known_verb_form(w)
            if info and info.get("tense") == "present" \
                    and not info.get("no_agreement"):
                verb_p, verb_n = PRESENT_PERSON_NUMBER.get(
                    _present_suffix_of(w, info), (None, None))
                subj = self._find_subject(words, i)
                if subj and verb_p is not None:
                    s_person, s_number = _pronoun_agreement(subj)
                    if s_person is not None and (s_person != verb_p
                                                 or s_number != verb_n):
                        expected = self._expected_form(info["stem"], s_person,
                                                       s_number)
                        errors.append(Diagnostic(
                            "R001", "error",
                            f"несогласованность подлежащего и сказуемого: "
                            f"'{subj}' / '{w}'",
                            suggestion=expected, line=lineno))
                # Проверяем каждое сказуемое: в предложении их может быть
                # несколько (сочинение, сложное предложение).

        # R001 для будущего времени: будем/будеш/...
        for i, w in enumerate(words):
            if w in FUTURE_PERSON_NUMBER and FUTURE_PERSON_NUMBER[w]:
                p, n = FUTURE_PERSON_NUMBER[w]
                subj = self._find_subject(words, i)
                s_person, s_number = _pronoun_agreement(subj) if subj else (None, None)
                if s_person is not None and (s_person != p or s_number != n):
                    errors.append(Diagnostic(
                        "R001", "error",
                        f"несогласованность подлежащего и вспомогательного '{w}'",
                        line=lineno))

        # R015 — числительное и число существительного (Rusido.md, 6.5).
        # Значение берётся по всему составному числительному, а не по
        # последнему слову: «двадек одн столи», но «сто одн столи».
        i = 0
        while i < len(words):
            value, end = self._numeral_phrase_value(words, i)
            if value is None or end >= len(words):
                i += 1
                continue
            nxt = self._known_noun_form(words[end])
            if nxt is not None:
                need_plural = value != 1
                has_plural = nxt["number"] == "plural"
                if need_plural != has_plural:
                    stem = nxt["root"].rstrip("ь")
                    expected = nouns.inflect_noun(
                        stem, "plural" if need_plural else "singular",
                        nxt["case"], grammar=self.grammar)
                    errors.append(Diagnostic(
                        "R015", "error",
                        f"нарушение правила числа после числительного "
                        f"'{' '.join(words[i:end])}': '{words[end]}'",
                        suggestion=expected, line=lineno))
            i = end + 1

        # R008 — прилагательное перед существительным (Rusido.md, 8.2)
        adj_stems = self._adj_stems()
        for i, w in enumerate(words):
            if w.endswith("ий") and w[:-2] in adj_stems:
                if i + 1 < len(words) and self._known_noun_form(words[i + 1]) is None \
                        and not self.lexicon.has(words[i + 1]):
                    warnings.append(Diagnostic(
                        "R008", "warning",
                        f"после прилагательного '{w}' ожидается существительное",
                        line=lineno))

        return errors, warnings

    # ---------- помощники ----------

    def _entries(self):
        return self.lexicon._by_lemma.values()

    def _noun_stems(self) -> list[str]:
        return [e.stem for e in self._entries() if e.pos == POS_NOUN]

    def _adj_stems(self) -> set[str]:
        return {e.stem for e in self._entries() if e.pos == POS_ADJ}

    def _verb_data(self):
        # Индексируем все алломорфы (Rusido.md, 7.1.1): ити → и / ид.
        stems, cons, inv = set(), set(), set()
        for e in self._entries():
            if e.pos == POS_VERB:
                stems.update(e.all_stems())
                if e.stem_type == "cons_stem":
                    cons.update(s for s in e.all_stems()
                                if s and not nouns.is_vowel(s[-1]))
                if e.meta.get("invariant"):
                    inv.add(e.lemma)
        return stems, cons, inv

    def _numeral_phrase_value(self, words: list[str],
                              start: int) -> tuple[int | None, int]:
        """Сумма подряд идущих числительных и индекс следующего слова."""
        total, i = 0, start
        while i < len(words):
            word = words[i]
            value = NUMERAL_VALUES.get(word)
            entry = self.lexicon.lookup(word)
            if value is None or entry is None or entry.pos != POS_NUM:
                break
            total += value
            i += 1
        if i == start:
            return None, start
        return total, i

    def _known_noun_form(self, word: str) -> dict | None:
        seg = nouns.segment_noun(word, self._noun_stems(), self.grammar)
        if seg is None:
            return None
        root, num_suf, case_suf = seg
        if self.grammar is not None:
            number = "singular" if num_suf == "" else                 next(k for k, v in self.grammar.noun_number.items() if v == num_suf)
            case = next(k for k, v in self.grammar.noun_case.items()
                        if v == case_suf)
        else:
            number = "plural" if num_suf == "и" else "singular"
            case = nouns.CASE_SUFFIXES_INV[case_suf]
        return {"root": root, "number": number, "case": case}

    def _known_verb_form(self, word: str) -> dict | None:
        stems, cons, inv = self._verb_data()
        return nouns.segment_verb(word, stems, cons, inv)

    def _find_subject(self, words: list[str], verb_index: int) -> str | None:
        for w in words[:verb_index]:
            if w in _PRONOUN_NOMINATIVE:
                return w
        return None

    def _expected_form(self, stem: str, person: int, number: str) -> str:
        entry_number = "singular" if number == "sg" else "plural"
        stem_type = "cons_stem" if stem in self._verb_data()[1] else "vowel_stem"
        return verbs.conjugate_present(stem, person, entry_number, stem_type,
                                     grammar=self.grammar)

    def _suggest(self, word: str) -> str | None:
        """Простейший движок исправлений: ближайшее словарное слово."""
        best, best_d = None, 3
        for lemma in self.lexicon._by_lemma:
            d = _levenshtein(word, lemma)
            if d < best_d:
                best, best_d = lemma, d
        return best


_PRONOUN_NOMINATIVE = {
    "я": (1, "sg"), "ти": (2, "sg"), "он": (3, "sg"),
    "ми": (1, "pl"), "ви": (2, "pl"), "они": (3, "pl"),
}

try:
    from rusido.morphology.numerals import NUMERAL_VALUES
except Exception:  # pragma: no cover
    NUMERAL_VALUES = {}


def _pronoun_agreement(word: str) -> tuple[int | None, str | None]:
    return _PRONOUN_NOMINATIVE.get(word, (None, None))


def _present_suffix_of(form: str, info: dict) -> str:
    stem = info["stem"]
    rest = form[len(stem):]
    if info.get("epenthetic"):
        rest = rest[1:]
    return rest


def _levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
