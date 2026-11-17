"""Тесты лексикона: критерий MVP — не менее 500 записей (README §15)."""

from rusido import Lexicon, RusidoValidator
from rusido.lexicon.dictionary import DEFAULT_LEXICON, POS_NOUN, LexiconEntry


def test_lexicon_size_mvp_criterion():
    assert len(DEFAULT_LEXICON) >= 500
    # Полный лексикон (включая data/lexicon/*.json) тоже удовлетворяет §15.
    assert len(Lexicon()) >= 500


def test_lexicon_len_and_contains():
    lex = Lexicon()
    assert len(lex) == len(lex._by_lemma)
    assert "идти" in lex
    assert "нет-такого-слова" not in lex


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


def test_allomorph_kinds_validated():
    from rusido.exceptions import InvalidFeatureError
    from rusido.lexicon.dictionary import ALLOMORPH_KINDS

    assert set(ALLOMORPH_KINDS) == {
        "infinitive", "present", "past", "imperative"}
    bad = LexiconEntry(lemma="идти", stem="ид", pos="verb",
                       allomorphs={"future": "ид"})
    try:
        Lexicon([bad])
    except InvalidFeatureError:
        pass
    else:
        raise AssertionError("неизвестный тип алломорфа должен отвергаться")

    entry = LexiconEntry(lemma="идти", stem="ид", pos="verb")
    entry.set_allomorph("infinitive", "и")
    assert entry.stem_for("infinitive") == "и"


def test_allomorph_end_to_end():
    """Алломорфы работают в переводчике, валидаторе и анализаторе."""
    from rusido import RusidoAnalyzer, RusidoTranslator

    translator = RusidoTranslator(use_nlp=False)
    assert translator.translate("идти").text == "ити"
    assert translator.translate("я иду").text == "я идем"

    validator = RusidoValidator()
    for form in ("ити", "идем", "идел", "иди"):
        assert validator.validate_word(form).valid, form

    analyzer = RusidoAnalyzer()
    assert any(item.pos == "verb" and item.root == "и"
               for item in analyzer.analyze("ити"))
    assert any(item.pos == "verb" and item.root == "ид"
               for item in analyzer.analyze("идем"))


def test_spec_function_words_in_lexicon():
    # §8.6 и §8.8: предлоги и частицы из спецификации должны быть словарными.
    lex = Lexicon()
    for word in ("под", "до"):
        assert lex.lookup(word).pos == "prep", word
    assert lex.lookup("же").pos == "particle"
    assert validator_word_valid(lex, "под")
    assert validator_word_valid(lex, "же")


def validator_word_valid(lex, word):
    from rusido import RusidoValidator
    return RusidoValidator(lexicon=lex).validate_word(word).valid


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
