"""Тесты валидатора Русидо (README.md, разделы 3.2 и 9)."""

import pytest


def test_valid_sentence(validator):
    report = validator.validate("Я читам книгу.")
    assert report.valid
    assert not report.errors


def test_invalid_word_code_r005(validator):
    report = validator.validate("Я вижу ковер.")
    codes = [e.code for e in report.errors]
    assert "R005" in codes
    assert not report.valid


def test_unknown_word_has_suggestion(validator):
    # опечатка без удвоенных согласных → R005 с ближайшим словарным словом
    report = validator.validate("книгуу.")
    diag = next(e for e in report.errors if e.code == "R005")
    assert diag.suggestion


def test_forbidden_letter_r006(validator):
    report = validator.validate("ёлка.")
    diag = next(e for e in report.errors if e.code == "R006")
    assert diag.suggestion == "елка"


def test_doubled_consonant_r007(validator):
    # удвоенные согласные запрещены (Rusido.md, 2.6)
    report = validator.validate("русский дом.")
    diag = next(e for e in report.errors if e.code == "R007")
    assert "сс" in diag.message
    assert diag.suggestion == "руский"
    assert validator.validate("руский дом.").valid


def test_agreement_error_r001(validator):
    # ми (1 л., мн. ч.) + читам (1 л., ед. ч.) — несогласованность
    report = validator.validate("Ми читам книгу.")
    assert any(e.code == "R001" for e in report.errors)


def test_agreement_valid(validator):
    assert validator.validate("Ми читами книгу.").valid
    assert validator.validate("Я читам книгу.").valid
    assert validator.validate("Ти читаш книгу.").valid
    assert validator.validate("Они читани книгу.").valid


def test_verb_forms_validate(validator):
    for form in ("читати", "читал", "читали", "читай", "читайте",
                 "идем", "идеш", "идет", "иди"):
        assert validator.validate_word(form).valid, form


def test_noun_forms_validate(validator):
    for form in ("книг", "книгу", "книги", "книгио", "дверь", "двери"):
        assert validator.validate_word(form).valid, form


def test_adjective_form_validates(validator):
    assert validator.validate_word("новий").valid


def test_service_words_validate(validator):
    for form in ("не", "и", "в", "на", "уже", "би"):
        assert validator.validate_word(form).valid, form


def test_numeral_number_rule_r015(validator):
    # «два» и больше требуют мн. ч. существительного (Rusido.md, 6.5)
    report = validator.validate("два книгу.")
    diag = next(e for e in report.errors if e.code == "R015")
    assert diag.suggestion == "книгиу"


def test_adjective_placement_warning_r008(validator):
    report = validator.validate("новий идет.")
    assert report.valid  # предупреждение, не ошибка
    assert any(w.code == "R008" for w in report.warnings)


def test_strict_mode_warns_without_final_punctuation():
    from rusido import RusidoValidator
    validator = RusidoValidator(strict=True)
    report = validator.validate("Я читам книгу")
    assert any(w.code == "R007" for w in report.warnings)


def test_report_counters(validator):
    report = validator.validate("Я читам книгу.\nОни идет.")
    assert report.tokens == 5
    assert report.sentences == 2


def test_validate_word_lowercases(validator):
    assert validator.validate_word("Книгу").valid


def test_diagnostics_property(validator):
    report = validator.validate("ёлка.")
    assert len(report.diagnostics) == len(report.errors) + len(report.warnings)


def test_spec_sample_text_validates(validator):
    """Образец текста из Rusido.md §11 проходит валидацию без ошибок."""
    sample = (
        "Мой брат жит в болший красивий доме. "
        "У нему ест два собаки. "
        "Я любим читати новий книгиу. "
        "Вчера я прочитал интересний книгу, кторий се писал од известний авторо. "
        "Завтра я будем писати письмо."
    )
    report = validator.validate(sample)
    assert report.valid, [(e.code, e.message) for e in report.errors]
