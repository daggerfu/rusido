"""Тесты нормализации орфографии (Rusido.md, раздел 2)."""

import pytest

from rusido.core.normalizer import (
    ALPHABET,
    FORBIDDEN_LETTERS,
    normalize_word,
)


def test_alphabet_has_29_letters():
    assert len(ALPHABET) == 29


def test_forbidden_letters_not_in_alphabet():
    for ch in FORBIDDEN_LETTERS:
        assert ch not in ALPHABET


@pytest.mark.parametrize("source,expected", [
    ("ёлка", "елка"),      # ё → е
    ("чёрный", "черний"),
    ("мышь", "мишь"),      # ы → и
    ("эхо", "ехо"),        # э → е
    ("объект", "обьект"),  # ъ → ь в любой позиции
    ("съезд", "сьезд"),
    ("съемка", "сьемка"),
    ("объявление", "обьявление"),
    ("класс", "клас"),     # удвоенные согласные сокращаются (Rusido.md, 2.6)
    ("агглютинативный", "аглютинативний"),
    ("русский", "руский"),
    ("длинный", "длиний"),
    ("касса", "каса"),
    ("книга", "книга"),    # обычное слово не меняется
    ("Ёлка", "Елка"),      # заглавные тоже нормализуются
])
def test_normalize_word(source, expected):
    assert normalize_word(source) == expected
