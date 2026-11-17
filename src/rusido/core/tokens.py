"""Внешние токены письменного текста (Rusido.md, §1.1, §2.7—2.9, §9.3).

Внутренний язык (лексика и морфология) не должен обрабатывать фрагменты,
которые являются числовой записью, аббревиатурой, оригинальным именем
или неадаптированным заимствованием. Здесь собраны чистые классификаторы
таких токенов без обращения к лексикону.
"""

from __future__ import annotations

import re

# Знаки, разрешённые Rusido.md §2.8 (используются тестами и CLI).
PUNCTUATION = set('. , ; : ? ! — - … « » " " ( ) [ ] /') - {" "}

_LATIN = re.compile(r"[a-z]", re.IGNORECASE)
_DIGIT = re.compile(r"\d")
_HYPHENATED_CASE = re.compile(r"-([уое])$", re.IGNORECASE)


def is_abbreviation(token: str) -> bool:
    """Все символы — заглавные буквы, их не менее двух: API, HTTP, БПМН.

    Знаки вроде '@' не являются частью аббревиатуры и должны попадать
    под отдельную диагностику R018.
    """
    return (len(token) >= 2 and token.isalpha()
            and all(ch.isupper() for ch in token))


def has_latin(token: str) -> bool:
    return bool(_LATIN.search(token))


def has_digit(token: str) -> bool:
    return bool(_DIGIT.search(token))


def hyphenated_case_suffix(token: str) -> str | None:
    """Падежный показатель оригинального имени: Анна-у → у."""
    match = _HYPHENATED_CASE.search(token)
    return match.group(1).lower() if match else None
