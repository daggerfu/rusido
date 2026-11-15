"""Алфавит Русидо и орфографическая нормализация (Rusido.md, раздел 2)."""

from __future__ import annotations

import re

# 29 букв; ё, ы, э, ъ в алфавите отсутствуют (Rusido.md, 2.1—2.2).
ALPHABET = "абвгдежзийклмнопрстуфхцчшщьюя"

FORBIDDEN_LETTERS = "ёыэъ"

# Русский «ъ» в любом случае заменяется на «ь» (объект → обьект,
# съезд → сьезд, съемка → сьемка).
_FORBIDDEN_MAP = {
    "ё": "е",
    "Ё": "Е",
    "Ы": "И",
    "ы": "и",
    "Э": "Е",
    "э": "е",
    "Ъ": "Ь",
    "ъ": "ь",
}

# Удвоенные согласные запрещены (Rusido.md, 2.6): две одинаковые согласные
# подряд сокращаются до одной.
DOUBLED_CONSONANT = re.compile(r"([бвгджзйклмнпрстфхцчшщ])\1", re.IGNORECASE)


def _collapse_doubled_consonants(text: str) -> str:
    while True:
        collapsed = DOUBLED_CONSONANT.sub(r"\1", text)
        if collapsed == text:
            return collapsed
        text = collapsed


def normalize_word(word: str) -> str:
    """Привести русское слово к орфографии Русидо.

    Правила (Rusido.md, 2.2 и 2.6): ё→е, ы→и, э→е, ъ→ь; удвоенные
    согласные сокращаются до одной.
    """
    text = word.translate(str.maketrans(_FORBIDDEN_MAP))
    return _collapse_doubled_consonants(text)
