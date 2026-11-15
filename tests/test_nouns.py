"""Тесты морфологии существительного (Rusido.md, раздел 3)."""

import pytest

from rusido.exceptions import InvalidFeatureError
from rusido.lexicon.dictionary import STEM_PALATAL
from rusido.morphology import nouns


def test_singular_nominative_has_no_suffixes():
    assert nouns.inflect_noun("книг") == "книг"


@pytest.mark.parametrize("case,suffix", [
    (nouns.ACCUSATIVE, "у"),
    (nouns.GENITIVE, "о"),
    (nouns.DATIVE, "е"),
])
def test_case_suffixes(case, suffix):
    assert nouns.inflect_noun("книг", case=case) == "книг" + suffix


def test_plural_suffix_before_case():
    assert nouns.inflect_noun("книг", number=nouns.PLURAL) == "книги"
    assert nouns.inflect_noun("книг", number=nouns.PLURAL,
                             case=nouns.GENITIVE) == "книгио"


def test_palatal_stem_drops_soft_sign():
    # мягкая основа хранится со знаком «ь»; перед гласным аффикса он выпадает
    assert nouns.inflect_noun("дверь", stem_type=STEM_PALATAL) == "двер"
    assert nouns.inflect_noun("дверь", number=nouns.PLURAL,
                              stem_type=STEM_PALATAL) == "двери"


def test_unknown_number_raises():
    with pytest.raises(InvalidFeatureError):
        nouns.inflect_noun("книг", number="dual")


def test_unknown_case_raises():
    with pytest.raises(InvalidFeatureError):
        nouns.inflect_noun("книг", case="instrumental")


@pytest.mark.parametrize("form,expected", [
    ("книг", ("книг", "", "")),
    ("книгу", ("книг", "", "у")),
    ("книги", ("книг", "и", "")),
    ("книгио", ("книг", "и", "о")),
    ("двери", ("двер", "и", "")),   # чередование мягкой основы
])
def test_segment_noun(form, expected):
    assert nouns.segment_noun(form, ["книг", "двер"]) == expected


def test_segment_noun_unknown_form():
    assert nouns.segment_noun("книгы", ["книг"]) is None


def test_segment_noun_prefers_longest_stem():
    assert nouns.segment_noun("имени", ["имен", "и"])[0] == "имен"
