"""Тесты прилагательных, числительных и разбора глагольных форм."""

from rusido.morphology import adjectives, numerals
from rusido.morphology.nouns import segment_verb


def test_adjective_suffix():
    assert adjectives.build_adjective("нов") == "новий"
    assert adjectives.ADJECTIVE_SUFFIX == "ий"


def test_degrees_are_analytic():
    assert adjectives.comparative("новий") == "более новий"
    assert adjectives.superlative("новий") == "самий новий"


def test_cardinals_cover_small_numbers():
    assert numerals.CARDINALS[1] == "одн"
    assert numerals.CARDINALS[5] == "пят"
    assert numerals.CARDINALS[11] == "однанадек"
    assert numerals.CARDINALS[20] == "двадек"
    assert numerals.CARDINALS[100] == "сто"


def test_ordinal_suffix():
    assert numerals.ordinal("два") == "дваим"


def test_required_noun_number():
    assert numerals.required_noun_number(1) == "singular"
    assert numerals.required_noun_number(2) == "plural"


def test_segment_verb_infinitive():
    assert segment_verb("читати", {"чита"}) == \
        {"stem": "чита", "mood": "infinitive"}


def test_segment_verb_present():
    info = segment_verb("читат", {"чита"})
    assert (info["tense"], info["person"], info["number"]) == \
        ("present", 3, "singular")


def test_segment_verb_epenthetic_e():
    info = segment_verb("идем", {"ид"}, {"ид"})
    assert info["stem"] == "ид"
    assert info["person"] == 1
    assert info["epenthetic"] is True


def test_segment_verb_past():
    assert segment_verb("читал", {"чита"}) == \
        {"stem": "чита", "tense": "past", "number": "singular"}
    assert segment_verb("читали", {"чита"})["number"] == "plural"


def test_segment_verb_imperative():
    assert segment_verb("читай", {"чита"}) == \
        {"stem": "чита", "mood": "imperative", "number": "singular"}
    assert segment_verb("читайте", {"чита"}) == \
        {"stem": "чита", "mood": "imperative", "number": "plural"}
    # «идите» строится как ид + и + те, но segment_verb его не разбирает
    assert segment_verb("идите", {"ид"}, {"ид"}) is None


def test_segment_verb_invariant():
    info = segment_verb("ест", set(), set(), {"ест"})
    assert info["no_agreement"] is True


def test_segment_verb_unknown():
    assert segment_verb("книга", {"чита"}) is None


def test_segment_verb_past_epenthetic():
    info = segment_verb("идел", {"ид"}, {"ид"})
    assert info["stem"] == "ид" and info["tense"] == "past" \
        and info.get("epenthetic")
