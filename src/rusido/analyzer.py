"""Морфологический анализатор Русидо (README.md, раздел 7.4).

Разбирает готовую форму Русидо по морфемам: ROOT + NUMBER + CASE и т.п.,
с опорой на лексикон (валидация идёт по морфемной структуре, а не по
«голым» окончаниям — README.md, 4.1).
"""

from __future__ import annotations

from dataclasses import dataclass

from rusido.lexicon.dictionary import POS_ADJ, POS_NOUN, POS_VERB, Lexicon
from rusido.morphology import nouns, verbs


@dataclass
class AnalysisItem:
    word: str
    pos: str | None = None
    root: str | None = None
    number: str | None = None
    case: str | None = None
    tense: str | None = None
    mood: str | None = None
    person: int | None = None
    morphemes: list[tuple[str, str]] | None = None
    valid: bool = False


class RusidoAnalyzer:
    def __init__(self, lexicon: Lexicon | None = None):
        self.lexicon = lexicon or Lexicon()

    def analyze(self, word: str) -> list[AnalysisItem]:
        return [self.analyze_word(w) for w in word.lower().split()]

    def analyze_word(self, word: str) -> AnalysisItem:
        if self.lexicon.has(word):
            entry = self.lexicon.lookup(word)
            item = AnalysisItem(word=word, pos=entry.pos, root=entry.stem,
                                valid=True)
            meta = entry.meta
            if entry.pos == POS_NOUN:
                item.number, item.case = nouns.SINGULAR, nouns.NOMINATIVE
            elif "person" in meta:
                item.person = meta["person"]
                item.number = "singular" if meta.get("number") == "sg" else "plural"
            return item

        # Существительное: ROOT + NUMBER + CASE
        noun_stems = [e.stem for e in self.lexicon._by_lemma.values()
                      if e.pos == POS_NOUN]
        seg = nouns.segment_noun(word, noun_stems)
        if seg is not None:
            root, num_suf, case_suf = seg
            return AnalysisItem(
                word=word, pos="noun", root=root,
                number=nouns.PLURAL if num_suf == "и" else nouns.SINGULAR,
                case=nouns.CASES_BY_SUFFIX[case_suf],
                morphemes=[(root, "ROOT"),
                           *(((num_suf, "PLURAL"),) if num_suf else ()),
                           *(((case_suf, nouns.CASES_BY_SUFFIX[case_suf].upper()),)
                             if case_suf else ())],
                valid=True,
            )

        # Глагол
        verb_stems, cons_stems = set(), set()
        for e in self.lexicon._by_lemma.values():
            if e.pos == POS_VERB:
                verb_stems.update(e.all_stems())
                if e.stem_type == "cons_stem":
                    cons_stems.update(s for s in e.all_stems()
                                      if s and not nouns.is_vowel(s[-1]))
        vinfo = nouns.segment_verb(word, verb_stems, cons_stems)
        if vinfo is not None:
            item = AnalysisItem(word=word, pos="verb", root=vinfo["stem"],
                                valid=True)
            if "mood" in vinfo:
                item.mood = vinfo["mood"]
            if "tense" in vinfo:
                item.tense = vinfo["tense"]
            item.person = vinfo.get("person")
            item.number = vinfo.get("number")
            return item

        # Прилагательное: основа + ий
        adj_stems = {e.stem for e in self.lexicon._by_lemma.values()
                     if e.pos == POS_ADJ}
        if word.endswith("ий") and word[:-2] in adj_stems:
            return AnalysisItem(word=word, pos="adj", root=word[:-2],
                                morphemes=[(word[:-2], "ROOT"), ("ий", "ADJ")],
                                valid=True)

        return AnalysisItem(word=word, valid=False)
