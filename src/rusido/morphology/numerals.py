"""Местоимения (Rusido.md, раздел 5) и числительные (раздел 6)."""

from __future__ import annotations

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

# 6.1—6.4 числительные
CARDINAL_SMALL = {
    0: "нол", 1: "одн", 2: "два", 3: "три", 4: "четир", 5: "пят",
    6: "шест", 7: "сем", 8: "восем", 9: "девят", 10: "десят",
}
TEENS = {11 + i: f"{base}надек"
         for i, base in enumerate(["одна", "два", "три", "четир", "пят",
                                   "шест", "сем", "восем", "девят"])}
TENS = {20 + 10 * i: f"{base}дек"
        for i, base in enumerate(["два", "три", "четир", "пят",
                                  "шест", "сем", "восем", "девят"])}
HUNDREDS = {100: "сто", 200: "двесто", 300: "тристо", 400: "четирсто", 500: "пятсто"}
THOUSANDS = {1000: "однтис", 2000: "дватис", 3000: "тритис",
             4000: "четиртис", 5000: "пяттис"}

CARDINALS = {}
CARDINALS.update(CARDINAL_SMALL, TEENS, TENS, HUNDREDS, THOUSANDS)

ORDINAL_SUFFIX = "им"  # 6.6: одним, дваим, триим...


def ordinal(cardinal_word: str) -> str:
    return cardinal_word + ORDINAL_SUFFIX


def required_noun_number(n: int) -> str:
    """Согласование (Rusido.md, 6.5): 1 — единственное, 2+ — множественное."""
    return "singular" if n == 1 else "plural"
