"""Три слоя письменного текста и цифровая запись (Rusido.md, §1.1, §6.7)."""

import pytest

from rusido import RusidoValidator


@pytest.fixture
def validator():
    return RusidoValidator()


# --- Внешние токены не проходят морфологию -------------------------------

def test_external_latin_token(validator):
    # Неадаптированное заимствование сохраняет написание (§9.3).
    assert validator.validate("software.").valid
    assert validator.validate("deadline.").valid
    assert validator.validate("machine learning.").valid
    assert validator.validate("Я читам API.").valid


def test_abbreviation_case_preserved(validator):
    # API не превращается в «апи»; правила удвоенных согласных не применяются.
    report = validator.validate("BPMN.")
    assert report.valid
    assert "bpmn" not in report.diagnostics[0].message if report.diagnostics else True


def test_original_name_with_case_suffix(validator):
    # Оригинальное имя получает падежный показатель через дефис (§2.9, §3.6).
    assert validator.validate("Я давам Анна-е.").valid
    assert validator.validate("Я давам Петров-у.").valid
    # Показатель ставится после последнего компонента полного имени.
    assert validator.validate_word("Петров-у").valid


def test_symbol_outside_alphabet_still_r018(validator):
    # Внутреннее слово с посторонним символом не считается внешним токеном.
    report = validator.validate("дом@")
    assert [d.code for d in report.errors] == ["R018"]


def test_forbidden_letters_in_uppercase_still_flagged(validator):
    report = validator.validate("ЁЛКА.")
    assert any(d.code == "R006" for d in report.errors)


# --- Цифровая запись и согласование (§6.7) -------------------------------

@pytest.mark.parametrize("text", [
    "0 столи.",
    "1 стол.",
    "2 столи.",
    "10 столи.",
    "21 столи.",
    "100 столи.",
    "1,0 стол.",
    "1,5 столи.",
    "3/4 столи.",
    "25% столи.",
    "1 000 столи.",
])
def test_numeric_agreement_valid(validator, text):
    report = validator.validate(text)
    assert report.valid, (text, report.errors)


@pytest.mark.parametrize("text,expected", [
    ("0 стол.", "столи"),
    ("1 столи.", "стол"),
    ("21 стол.", "столи"),
    ("1,5 стол.", "столи"),
    ("1,0 столи.", "стол"),
])
def test_numeric_agreement_error(validator, text, expected):
    report = validator.validate(text)
    diag = next(e for e in report.errors if e.code == "R015")
    assert diag.suggestion == expected, text


def test_special_numeric_formats_no_false_positive(validator):
    assert validator.validate("17.11.2026").valid
    assert validator.validate("15:30").valid
    assert validator.validate("10–20").valid


# --- Экзистенциальный предикатор «ест» (§8.3) ----------------------------

def test_est_is_invariant_predicator(validator):
    for text in ("У мне ест книга.", "У нему ест два собаки.",
                 "У они ест новий дом."):
        assert validator.validate(text).valid, text
