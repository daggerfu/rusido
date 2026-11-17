"""Местоимения (Rusido.md, раздел 5) и числительные (раздел 6)."""

from __future__ import annotations

from rusido.core.normalizer import DOUBLED_CONSONANT

# 5.1 личные (именительный) и 5.2 косвенные формы
PERSONAL_NOMINATIVE = {
    (1, "sg"): "я", (2, "sg"): "ти", (3, "sg"): "он",
    (1, "pl"): "ми", (2, "pl"): "ви", (3, "pl"): "они",
}
PERSONAL_OBLIQUE = {
    (1, "sg"): "мне", (2, "sg"): "тебе", (3, "sg"): "нему",
    (1, "pl"): "нам", (2, "pl"): "вам", (3, "pl"): "ним",
}
POSSESSIVE = ["мой", "твой", "его", "наш", "ваш", "их"]
DEMONSTRATIVE = ["етот", "тот", "такой"]

ALL_PRONOUNS = set(PERSONAL_NOMINATIVE.values()) | set(PERSONAL_OBLIQUE.values()) \
    | set(POSSESSIVE) | set(DEMONSTRATIVE) | {"се"}

# 6.1—6.5 числительные
CARDINAL_SMALL = {
    0: "нол", 1: "одн", 2: "два", 3: "три", 4: "четир", 5: "пят",
    6: "шест", 7: "сем", 8: "восем", 9: "девят", 10: "десят",
}

# Разрядные показатели (Rusido.md, 6.2—6.4).
TEEN_SUFFIX = "надек"
TEN_SUFFIX = "дек"
HUNDRED_SUFFIX = "сто"
THOUSAND_SUFFIX = "тис"


def _join(base: str, suffix: str) -> str:
    """Основа + разрядный показатель; удвоенные согласные сокращаются (§2.6)."""
    return DOUBLED_CONSONANT.sub(r"\1", base + suffix)


# 11 = одн + надек → одннадек → однадек (§6.2, §2.6).
TEENS = {11 + i: _join(base, TEEN_SUFFIX)
         for i, base in enumerate(["одн", "два", "три", "четир", "пят",
                                   "шест", "сем", "восем", "девят"])}
TENS = {20 + 10 * i: _join(base, TEN_SUFFIX)
        for i, base in enumerate(["два", "три", "четир", "пят",
                                  "шест", "сем", "восем", "девят"])}
HUNDREDS = {
    100: "сто",  # 100 — отдельная форма (§6.4), не «однсто»
    **{100 * i: _join(CARDINAL_SMALL[i], HUNDRED_SUFFIX)
       for i in range(2, 10)},
}
THOUSANDS = {1000 * i: _join(CARDINAL_SMALL[i], THOUSAND_SUFFIX)
             for i in range(1, 10)}

CARDINALS: dict[int, str] = {}
for _table in (CARDINAL_SMALL, TEENS, TENS, HUNDREDS, THOUSANDS):
    CARDINALS.update(_table)
del _table

# Обратный индекс для разбора составного числительного и R015.
NUMERAL_VALUES = {word: value for value, word in CARDINALS.items()}

MAX_CARDINAL = 9999

ORDINAL_SUFFIX = "им"  # 6.6: одним, дваим, триим...


def cardinal(n: int) -> str:
    """Число 0—9999 из разрядов (Rusido.md, 6.1—6.4).

    Ненулевые разряды перечисляются через пробел в порядке убывания;
    11—19 — отдельные слова с суффиксом `-надек`. Вне диапазона число
    записывается цифрами.
    """
    if not 0 <= n <= MAX_CARDINAL:
        return str(n)
    if n in CARDINALS:
        return CARDINALS[n]

    parts = []
    for size, table in ((1000, THOUSANDS), (100, HUNDREDS), (10, TENS)):
        count = n // size
        if count:
            parts.append(table[count * size])
            n -= count * size
    if n:
        parts.append(CARDINAL_SMALL[n])
    return " ".join(parts)


def ordinal(cardinal_word: str) -> str:
    """Порядковое числительное: `-им` к последнему компоненту (§6.6)."""
    return cardinal_word + ORDINAL_SUFFIX


def ordinal_number(n: int) -> str:
    """Порядковое от числа: сто двадек пят → сто двадек пятим."""
    if not 0 <= n <= MAX_CARDINAL:
        return str(n)
    return ordinal(cardinal(n))


def required_noun_number(n: int) -> str:
    """Согласование (Rusido.md, 6.5): 1 — единственное, 0 и 2+ — множественное."""
    return "singular" if n == 1 else "plural"
