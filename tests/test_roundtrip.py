"""Сквозной тест целостности: вывод переводчика проходит валидацию
(README.md, раздел 11)."""

import pytest

# Фразы, собранные из слов и форм, известных лексикону и морфологии MVP.
ROUNDTRIP_CASES = [
    "Я читам книгу.",
    "Ми читами книги.",
    "Ти идеш дом.",
    "Я читал книгу.",
    "Я читал новий книгу.",
]


@pytest.mark.parametrize("text", ROUNDTRIP_CASES)
def test_translation_validates(text, translator, validator):
    result = translator.translate(text)
    report = validator.validate(result.text)
    assert report.valid, \
        f"{text!r} → {result.text!r}: " + \
        ", ".join(f"{e.code} {e.message}" for e in report.errors)
