"""Тесты переводчика русский → Русидо (README.md, раздел 7.2).

Фикстура `translator` использует NLP (pymorphy3), если он установлен;
`heuristic_translator` — чистые эвристики MVP (use_nlp=False).
"""

import pytest

from rusido.lexicon.dictionary import POS_NOUN, POS_PRON, POS_VERB
from rusido.morphology.nouns import DATIVE, PLURAL, SINGULAR


def test_noun_cases(translator):
    # NLP-разбор: именительный → ∅, винительный → -у
    assert translator.translate("книга").text == "книг"
    assert translator.translate("книгу").text == "книгу"


def test_noun_plural(translator):
    assert translator.translate("собаки").text == "собаки"


def test_verb_infinitive(translator):
    assert translator.translate("читать").text == "читати"
    assert translator.translate("идти").text == "ити"  # орфография: идти → ити


def test_verb_present_person(translator):
    # глагольные формы настоящего времени переводятся через NLP-разбор
    assert translator.translate("читаю").text == "читам"
    assert translator.translate("читает").text == "читат"
    assert translator.translate("читаем").text == "читами"
    assert translator.translate("иду").text == "идем"       # соединительная е
    assert translator.translate("идешь").text == "идеш"


def test_verb_past(translator):
    assert translator.translate("читал").text == "читал"
    assert translator.translate("читали").text == "читали"


def test_verb_imperative(translator):
    assert translator.translate("иди").text == "иди"
    assert translator.translate("идите").text == "идите"
    assert translator.translate("читай").text == "читай"
    assert translator.translate("читайте").text == "читайте"


def test_verb_allomorphs(translator):
    # Инфинитивная основа «и-», остальные алломорфы «ид-» (Rusido.md, 7.1.1).
    assert translator.translate("идти").text == "ити"
    assert translator.translate("иду").text == "идем"
    assert translator.translate("идет").text == "идет"
    assert translator.translate("идел").text == "идел"
    assert translator.translate("идели").text == "идели"
    assert translator.translate("иди").text == "иди"
    assert translator.translate("идите").text == "идите"


def test_future_with_infinitive(translator):
    # Личная форма будти + инфинитив основного глагола (Rusido.md, 7.4).
    assert translator.translate("буду идти").text == "будем ити"
    assert translator.translate("будем идти").text == "будеми ити"
    assert translator.translate("будет идти").text == "будет ити"
    assert translator.translate("будет читать").text == "будет читати"
    # Без следующего инфинитива вспомогательный сохраняет «будти».
    assert translator.translate("будет").text == "будет будти"


def test_adjective_override(translator):
    # основа «болш» хранится в лексиконе → форма «болший»
    assert translator.translate("большой").text == "болший"


def test_pronoun_is_invariant(translator):
    assert translator.translate("я").text == "я"
    assert translator.translate("они").text == "они"


def test_capitalization_preserved(translator):
    assert translator.translate("Книгу").text == "Книгу"
    result = translator.translate("Я читал книгу.")
    assert result.text.startswith("Я ")


def test_unknown_word_normalized(translator):
    # неизвестное слово проходит орфонормализацию и снижает confidence
    result = translator.translate("партия")
    assert result.text == "партия"
    assert result.confidence < 1.0


def test_confidence_full_match(translator):
    assert translator.translate("книга").confidence == 1.0


def test_translate_batch(translator):
    results = translator.translate_batch(["книгу", "дом"])
    assert [r.text for r in results] == ["книгу", "дом"]


def test_result_metadata(translator):
    result = translator.translate("книга")
    assert result.source == "книга"
    assert result.grammar_version == "1.0"
    assert isinstance(result.warnings, list)


# --- эвристики MVP (use_nlp=False) ---

def test_heuristic_noun_cases(heuristic_translator):
    # Эвристика: -а без контекста → им. п., -у → вин. п.
    assert heuristic_translator.translate("книга").text == "книг"
    assert heuristic_translator.translate("книгу").text == "книгу"


def test_heuristic_object_after_verb(heuristic_translator):
    # По SVO слово после глагола — объект; после вспомогательного — нет.
    assert heuristic_translator.translate("я вижу собака").text == "я вижу собаку"
    assert heuristic_translator.translate("завтра будет книга").text == \
        "завтра будет книг"


def test_heuristic_instrumental_to_dative():
    # Русский творительный передаётся дательным — постоянное правило (D-013).
    from rusido.translation.translator import _guess_ru_case
    assert _guess_ru_case("домом", "домом") == DATIVE


def test_heuristic_number_ignores_non_nouns():
    # -и/-ы не означают мн. ч. у глаголов, прилагательных и местоимений.
    from rusido.translation.translator import _guess_ru_number
    assert _guess_ru_number("деньги", POS_NOUN) == PLURAL
    assert _guess_ru_number("читали", POS_VERB) == SINGULAR
    assert _guess_ru_number("они", POS_PRON) == SINGULAR
    assert _guess_ru_number("остров", POS_NOUN) == SINGULAR


def test_heuristic_plural_guess(heuristic_translator):
    # русское множественное окончание -и → мн. ч. Русидо
    assert heuristic_translator.translate("книги").text == "книги"


def test_heuristic_palatal_stem_noun(heuristic_translator):
    assert heuristic_translator.translate("дверь").text == "двер"
    # форма мн. ч. «двери» неизвестна лексикону как лемма — остаётся как есть
    assert heuristic_translator.translate("двери").text == "двери"


def test_heuristic_punctuation_preserved(heuristic_translator):
    result = heuristic_translator.translate("Я читал книгу, дома.")
    assert result.text == "Я читал книгу, дома."


def test_unknown_word_adds_warning(translator):
    result = translator.translate("Я вижу партия.")
    assert any("партия" in w for w in result.warnings)
    # известные слова предупреждений не порождают
    assert translator.translate("книга").warnings == []
