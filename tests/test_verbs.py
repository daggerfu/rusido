"""Тесты морфологии глагола (Rusido.md, раздел 7)."""

import pytest

from rusido.exceptions import InvalidFeatureError
from rusido.lexicon.dictionary import VERB_CONSONANT, VERB_VOWEL
from rusido.morphology import verbs


def test_infinitive():
    assert verbs.infinitive("чита") == "читати"


@pytest.mark.parametrize("person,number,expected", [
    (1, "singular", "читам"), (2, "singular", "читаш"),
    (3, "singular", "читат"), (1, "plural", "читами"),
    (2, "plural", "читате"), (3, "plural", "читани"),
])
def test_conjugate_present_vowel_stem(person, number, expected):
    assert verbs.conjugate_present("чита", person, number,
                                   VERB_VOWEL) == expected


@pytest.mark.parametrize("person,number,expected", [
    (1, "singular", "идем"), (2, "singular", "идеш"),
    (3, "singular", "идет"), (3, "plural", "идени"),
])
def test_conjugate_present_consonant_stem_inserts_e(person, number, expected):
    # соединительная гласная «е» при основе на согласный (Rusido.md, 7.2)
    assert verbs.conjugate_present("ид", person, number,
                                   VERB_CONSONANT) == expected


def test_conjugate_past():
    assert verbs.conjugate_past("чита") == "читал"
    assert verbs.conjugate_past("чита", "plural") == "читали"


def test_conjugate_future():
    assert verbs.conjugate_future(3, "singular", "читати") == "будет читати"
    assert verbs.conjugate_future(2, "plural", "читати") == "будете читати"


def test_all_future_forms():
    expected = {"будем", "будеш", "будет", "будеми", "будете", "будени"}
    forms = {verbs.FUTURE_FORMS[(p, n)]
             for p in (1, 2, 3) for n in ("sg", "pl")}
    assert forms == expected


def test_imperative():
    assert verbs.imperative("чита") == "читай"          # основа на гласный + й
    assert verbs.imperative("чита", plural=True) == "читайте"
    assert verbs.imperative("ид", stem_type=VERB_CONSONANT) == "иди"
    assert verbs.imperative("ид", plural=True,
                            stem_type=VERB_CONSONANT) == "идите"


def test_conditional():
    assert verbs.conditional("чита") == "би читал"
    assert verbs.conditional("чита", "plural") == "би читали"


def test_negate():
    assert verbs.negate("читат") == "не читат"


def test_invalid_combination_raises():
    with pytest.raises(InvalidFeatureError):
        verbs.conjugate_present("чита", 4, "singular")
    with pytest.raises(InvalidFeatureError):
        verbs.conjugate_past("чита", "dual")
    with pytest.raises(InvalidFeatureError):
        verbs.conjugate_future(4, "singular", "читати")
