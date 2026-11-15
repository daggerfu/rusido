"""Тесты лексикона: критерий MVP — не менее 500 записей (README §15)."""

from rusido import Lexicon, RusidoValidator
from rusido.lexicon.dictionary import DEFAULT_LEXICON


def test_lexicon_size_mvp_criterion():
    assert len(DEFAULT_LEXICON) >= 500


def test_no_duplicate_lemmas():
    lemmas = [e.lemma for e in DEFAULT_LEXICON]
    assert len(lemmas) == len(set(lemmas))


def test_every_lemma_validates(validator=None):
    validator = validator or RusidoValidator()
    bad = [e.lemma for e in DEFAULT_LEXICON
           if not validator.validate_word(e.lemma).valid]
    assert bad == []


def test_bootstrap_words_translatable():
    from rusido import RusidoTranslator
    t = RusidoTranslator(use_nlp=False)
    assert t.translate("гора").text == "горо"      # эвристика: -а → род. п.
    assert t.translate("гулять").text == "гуляти"
    assert t.translate("теплый").text == "теплий"


def test_lexicon_lookup_new_entries():
    lexicon = Lexicon()
    assert lexicon.lookup("гора").stem == "гор"
    assert lexicon.lookup("гулять").source_form == "гуляти"
