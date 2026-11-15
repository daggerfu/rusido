"""Тесты YAML-грамматики: загрузка и согласованность с кодом (README §10)."""

from rusido.core import grammar as grammar_module
from rusido.core.normalizer import ALPHABET, FORBIDDEN_LETTERS
from rusido.morphology import adjectives, nouns, verbs


def test_load_default_grammar():
    profile = grammar_module.load_grammar()
    assert profile.version == "1.0"
    assert profile.default_order == "SVO"


def test_yaml_matches_code_constants():
    """YAML-грамматика и константы морфологии не должны расходиться."""
    g = grammar_module.load_grammar()
    assert g.alphabet == ALPHABET
    assert "".join(g.forbidden) == FORBIDDEN_LETTERS
    assert g.noun_number == nouns.NUMBER_SUFFIXES
    assert g.noun_case == nouns.CASE_SUFFIXES
    assert g.verb_infinitive_suffix == "ти"
    assert g.present_sg == list(verbs.PRESENT_SG)
    assert g.present_pl == list(verbs.PRESENT_PL)
    assert g.past_sg == verbs.PAST_SINGULAR
    assert g.past_pl == verbs.PAST_PLURAL
    assert g.epenthetic_vowel == "е"
    assert g.adjective_suffix == adjectives.ADJECTIVE_SUFFIX


def test_yaml_grammar_can_generate_forms():
    """Формы, построенные по таблицам YAML, совпадают с морфологией."""
    g = grammar_module.load_grammar()
    assert "книг" + g.noun_number["plural"] + g.noun_case["accusative"] \
        == nouns.inflect_noun("книг", nouns.PLURAL, nouns.ACCUSATIVE)


def test_custom_grammar_version_changes_output(tmp_path):
    """grammar_version работает по-настоящему: кастомный YAML меняет формы."""
    import yaml
    data = yaml.safe_load(
        grammar_module.DEFAULT_GRAMMAR_PATH.read_text(encoding="utf-8"))
    data["language"]["version"] = "9.9"
    data["noun"]["case"]["accusative"] = "ун"   # вместо -у
    data["adjective"]["suffix"] = "ая"
    path = tmp_path / "grammar_9_9.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    grammar = grammar_module.load_grammar(path)
    assert grammar.version == "9.9"

    from rusido import RusidoTranslator, RusidoValidator
    translator = RusidoTranslator(grammar=grammar)
    assert translator.grammar_version == "9.9"
    assert translator.translate("книгу").text == "книгун"
    assert translator.translate("новый").text == "новая"

    # валидатор принимает формы новой версии и отклоняет старые
    validator = RusidoValidator(grammar=grammar)
    assert validator.validate("книгун.").valid
    assert not validator.validate("книгу.").valid
