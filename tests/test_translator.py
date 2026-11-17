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


def test_syncretism_nominative_without_context(translator):
    # Частотная гипотеза pymorphy3 неверна без контекста (D-024):
    # «книги» → род. ед., «дверь» → вин. ед.; подлежащее — именительный.
    assert translator.translate("книги").text == "книги"
    assert translator.translate("столы").text == "столи"
    assert translator.translate("дверь").text == "двер"


def test_intransitive_verb_does_not_create_object(translator):
    # D-026: «идти/жить/спать» не открывают винительный объект по SVO.
    assert translator.translate("я иду дом").text == "я идем дом"
    assert translator.translate("он живет город").text == "он жит город"
    assert translator.translate("я сплю собака").text == "я спам собак"


def test_transitive_verb_still_creates_object(translator):
    assert translator.translate("я читаю книгу").text == "я читам книгу"
    assert translator.translate("я вижу собаку").text == "я видем собаку"


def test_syncretism_accusative_after_verb(translator):
    # После переходного глагола (SVO) та же форма — объект → винительный.
    assert translator.translate("я читаю книги").text == "я читам книгиу"
    assert translator.translate("я вижу столы").text == "я видем столиу"
    assert translator.translate("я открываю дверь").text == "я откривам дверу"


def test_syncretism_subject_before_verb(translator):
    # Подлежащее перед глаголом остаётся именительным, хоть pymorphy3
    # видит в «дверь» винительный падеж.
    assert translator.translate("дверь открыта").text == "двер открита"


def test_preposition_governance_overrides_pymorphy3(translator):
    # Управление Русидо (§8.6, D-009) отличается от русского: «у» требует
    # дательного, хотя pymorphy3 даёт родительный.
    assert translator.translate("у книги").text == "у книге"
    # «в/на» неоднозначны: падеж определяет форма существительного.
    assert translator.translate("в доме").text == "в доме"
    assert translator.translate("на столе").text == "на столе"


def test_preposition_pod_takes_dative(translator):
    # Rusido.md §8.6: под столом → под столе (статическое местоположение).
    assert translator.translate("под столом").text == "под столе"


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
    # Без инфинитива — самостоятельная связочная форма (Rusido.md §7.4, D-025).
    assert translator.translate("будет").text == "будет"


def test_future_copula_nominal_predicate(translator):
    # §7.4: именная/качественная часть не несёт русского падежного окончания.
    assert translator.translate("Он будет студентом").text == "Он будет студент"
    assert translator.translate("Я буду аналитиком").text == "Я будем аналитик"
    assert translator.translate("Мы будем специалистами").text == \
        "Ми будеми специалисти"
    assert translator.translate("Дом будет красивым").text == "Дом будет красивий"


def test_future_existential_predicate(translator):
    # §8.3: будти согласуется с обладаемым объектом по числу.
    assert translator.translate("У меня будет книга").text == "У мне будет книг"
    assert translator.translate("У него будет дом").text == "У нему будет дом"
    assert translator.translate("У них будут собаки").text == \
        "У ним будени собаки"
    assert translator.translate("Завтра будет дождь").text == "Завтра будет дожд"


def test_existential_present_predicate_invariant(translator):
    # §8.3: «ест» — неизменяемый предикатор, а не форма глагола «ести».
    assert translator.translate("У меня ест книга").text == "У мне ест книг"


def test_future_action_keeps_infinitive(translator):
    # §7.4: в вспомогательной конструкции инфинитив — отдельное слово.
    assert translator.translate("Он будет читать").text == "Он будет читати"
    assert translator.translate("Я буду работать").text == "Я будем работати"
    assert translator.translate("Они будут строить").text == "Они будени строити"


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


def test_service_word_overrides(translator):
    # Закрытый набор служебных слов (Rusido.md, 2.2) не выводится
    # нормализацией и задаётся таблицей RU_TO_LEMMA_OVERRIDES.
    assert translator.translate("что").text == "што"
    assert translator.translate("чтобы").text == "штоби"
    assert translator.translate("который").text == "кторий"
    assert translator.translate("ещё").text == "ешо"


def test_syncretism_resolved_by_context(translator):
    # Снятие синкретизма падежей по контексту (D-024): гипотеза pymorphy3
    # выбирается управлением предлога / позицией объекта, а не частотой.
    assert translator.translate("Я читаю книги.").text == "Я читам книгиу."
    assert translator.translate("Книги лежат на столе.").text.startswith("Книги ")
    assert translator.translate("Я вижу брата.").text == "Я видем брату."


def test_predicate_net_governs_genitive(translator):
    # «нет» управляет родительным (Rusido.md, 8.4): книга → книго.
    assert translator.translate("У меня нет книги.").text == "У мне нет книго."


def test_pronoun_oblique_after_preposition(translator):
    # Дательные предлоги требуют косвенной формы местоимения (§5.2, §8.6):
    # русское «у меня/нас/них» → «у мне/нам/ним».
    assert translator.translate("Я иду к тебе.").text == "Я идем к тебе."
    assert translator.translate("У них нет собаки.").text == "У ним нет собако."
