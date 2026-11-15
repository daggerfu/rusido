"""Алфавит Русидо и орфографическая нормализация (Rusido.md, раздел 2)."""

from __future__ import annotations

# 29 букв; ё, ы, э, ъ в алфавите отсутствуют (Rusido.md, 2.1—2.2).
ALPHABET = "абвгдежзийклмнопрстуфхцчшщьюя"

FORBIDDEN_LETTERS = "ёыэъ"

# Русский «ъ» на конце после велярных (г/к/х) перед согласной переходит в «ь»
# (объект → обьект, съезд → сьезд); в остальных позициях он просто удаляется.
_FORBIDDEN_MAP = {
    "ё": "е",
    "Ы": "И",
    "ы": "и",
    "Э": "Е",
    "э": "е",
    "Ъ": "",
    "ъ": "",
}

_VELAR_CONSONANTS = "гкх"
_POST_VELEAR_CONSONANTS = "бвгдджзклмнпрстфхцчшщ"


def _convert_trailing_hard_sign(text: str) -> str:
    out = []
    for i, ch in enumerate(text):
        if ch in ("Ъ", "ъ"):
            prev = text[i - 1].lower() if i > 0 else ""
            nxt = text[i + 1].lower() if i + 1 < len(text) else ""
            if prev in _VELAR_CONSONANTS and nxt in _POST_VELEAR_CONSONANTS:
                out.append("ь" if ch == "ъ" else "Ь")
                continue
            continue  # удаление
        out.append(ch)
    return "".join(out)


def normalize_word(word: str) -> str:
    """Привести русское слово к орфографии Русидо.

    Правила (Rusido.md, 2.2): ё→е, ы→и, э→е; ъ отпадает, кроме позиции
    после г/к/х перед согласной, где он заменяется на мягкий знак.
    """
    mapped = word.translate(str.maketrans(_FORBIDDEN_MAP))
    return _convert_trailing_hard_sign(mapped)
