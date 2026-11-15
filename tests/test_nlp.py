"""Тесты NLP-интеграции (pymorphy3, rusido/core/nlp.py)."""

import pytest

pymorphy3 = pytest.importorskip("pymorphy3", reason="pymorphy3 не установлен")

from rusido.core.nlp import RussianMorphAnalyzer  # noqa: E402
from rusido import RusidoTranslator  # noqa: E402


def test_analyzer_available():
    assert RussianMorphAnalyzer().available


def test_translator_nlp_flag():
    assert RusidoTranslator().nlp_available
    assert not RusidoTranslator(use_nlp=False).nlp_available


def test_analyze_noun():
    a = RussianMorphAnalyzer().analyze("книгу")
    assert a.lemma == "книга"
    assert a.pos == "NOUN"
    assert a.case == "accusative"
    assert a.number == "singular"


def test_analyze_verb():
    a = RussianMorphAnalyzer().analyze("читали")
    assert a.lemma == "читать"
    assert a.pos == "VERB"
    assert a.tense == "past"
    assert a.number == "plural"


def test_analyze_imperative():
    a = RussianMorphAnalyzer().analyze("читай")
    assert a.mood == "imperative"
    assert a.number == "singular"


def test_accept_lemma_prefers_lexicon_parse():
    # без фильтра первая гипотеза — прилагательное «читаемый»
    a = RussianMorphAnalyzer()
    assert a.analyze("читаем").pos == "ADJS"
    picked = a.analyze("читаем", accept_lemma=lambda lemma: lemma == "читать")
    assert picked.pos == "VERB"
    assert picked.person == 1
    assert picked.number == "plural"


def test_case_mapping_ablt_to_dative():
    # творительный отображается на дательный (README.md §13)
    a = RussianMorphAnalyzer().analyze("книгой")
    assert a.case == "dative"


def test_abbr_parse_does_not_hijack_single_letter():
    # «е» — буква алфавита, не аббревиатура глагола «быть» (баг «бует»)
    translator = RusidoTranslator()
    assert translator.translate("А Б В Г Д Е Ж").text == "А Б В Г Д Е Ж"
    assert translator.translate("е").text == "е"
