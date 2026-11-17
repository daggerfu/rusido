"""Тесты лексикона: критерий MVP — не менее 500 записей (README §15)."""

from rusido import Lexicon, RusidoValidator
from rusido.lexicon.dictionary import DEFAULT_LEXICON, POS_NOUN, LexiconEntry


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
    assert t.translate("гора").text == "гор"       # эвристика: -а → им. п. без контекста
    assert t.translate("гулять").text == "гуляти"
    assert t.translate("теплый").text == "теплий"


def test_json_roundtrip():
    lex = Lexicon([LexiconEntry(lemma="тест", stem="тест", pos=POS_NOUN)])
    restored = Lexicon.from_json(lex.to_json())
    assert restored.lookup("тест").stem == "тест"
    assert restored.lookup_form("читати") is None  # из JSON не подхватываем встроенные


def test_allomorph_stems():
    entry = Lexicon().lookup("идти")
    assert entry.stem_for("infinitive") == "и"
    for kind in ("present", "past", "imperative"):
        assert entry.stem_for(kind) == "ид"
    assert entry.all_stems() == {"и", "ид"}

    # Неуказанные алломорфы совпадают с основной основой.
    plain = LexiconEntry(lemma="читать", stem="чита", pos="verb")
    assert plain.stem_for("past") == "чита"
    assert plain.all_stems() == {"чита"}


def test_json_roundtrip_allomorphs():
    entry = LexiconEntry(lemma="идти", stem="ид", pos="verb",
                         allomorphs={"infinitive": "и"})
    restored = Lexicon.from_json(Lexicon([entry]).to_json())
    assert restored.lookup("идти").allomorphs == {"infinitive": "и"}


def test_external_dictionaries_loaded():
    lex = Lexicon()
    for lemma in ("вишня", "метро", "телефон"):
        assert lex.has(lemma), lemma
    assert not Lexicon(load_external=False).has("вишня")


def test_lookup_form_index():
    lex = Lexicon()
    assert lex.lookup_form("читати").lemma == "читать"
    assert lex.lookup_form("болший").lemma == "большой"


def test_lexicon_lookup_new_entries():
    lexicon = Lexicon()
    assert lexicon.lookup("гора").stem == "гор"
    assert lexicon.lookup("гулять").source_form == "гуляти"
