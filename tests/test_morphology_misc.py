"""Тесты прилагательных, числительных и разбора глагольных форм."""

from rusido.lexicon import Lexicon
from rusido.lexicon.dictionary import VERB_CONSONANT, VERB_VOWEL
from rusido.morphology import adjectives, numerals, verbs
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
    assert numerals.CARDINALS[11] == "однадек"
    assert numerals.CARDINALS[12] == "дванадек"
    assert numerals.CARDINALS[20] == "двадек"
    assert numerals.CARDINALS[100] == "сто"


def test_cardinals_match_lexicon():
    # Лексикон и R015 не должны расходиться с генератором числительных.
    lexicon = Lexicon()
    for value, word in numerals.CARDINALS.items():
        assert lexicon.has(word), (value, word)


def test_ordinal_suffix():
    assert numerals.ordinal("два") == "дваим"


def test_composite_cardinal_and_ordinal():
    # Разряды 0—9999 собираются композиционно (Rusido.md, 6.4; D-017).
    assert numerals.cardinal(21) == "двадек одн"
    assert numerals.cardinal(125) == "сто двадек пят"
    assert numerals.cardinal(600) == "шестсто"
    assert numerals.cardinal(1001) == "однтис одн"
    assert numerals.cardinal(2026) == "дватис двадек шест"
    assert numerals.cardinal(7650) == "семтис шестсто пятдек"
    # Удвоенные согласные сокращаются (§2.6): одн+надек, пят+тис.
    assert numerals.cardinal(11) == "однадек"
    assert numerals.cardinal(5000) == "пятис"
    assert numerals.cardinal(10000) == "10000"

    # -им присоединяется к последнему компоненту (Rusido.md, 6.6).
    assert numerals.ordinal_number(125) == "сто двадек пятим"
    assert numerals.ordinal_number(23) == "двадек триим"


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
    # «идите» строится как ид + и + те (Rusido.md, 7.5)
    assert segment_verb("идите", {"ид"}, {"ид"}) == \
        {"stem": "ид", "mood": "imperative", "number": "plural"}
    assert segment_verb("иди", {"ид"}, {"ид"}) == \
        {"stem": "ид", "mood": "imperative", "number": "singular"}


def test_imperative_generator_and_parser_agree():
    for stem, stem_type, stems, consonant_stems in (
        ("чита", VERB_VOWEL, {"чита"}, set()),
        ("ид", VERB_CONSONANT, set(), {"ид"}),
    ):
        for plural, number in ((False, "singular"), (True, "plural")):
            form = verbs.imperative(stem, plural=plural, stem_type=stem_type)
            assert segment_verb(form, stems, consonant_stems) == {
                "stem": stem, "mood": "imperative", "number": number,
            }, form


def test_segment_verb_invariant():
    info = segment_verb("ест", set(), set(), {"ест"})
    assert info["no_agreement"] is True


def test_segment_verb_unknown():
    assert segment_verb("книга", {"чита"}) is None


def test_segment_verb_past_epenthetic():
    info = segment_verb("идел", {"ид"}, {"ид"})
    assert info["stem"] == "ид" and info["tense"] == "past" \
        and info.get("epenthetic")
