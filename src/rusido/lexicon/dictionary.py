"""Лексикон Русидо (README.md, 4.5; Rusido.md, разделы 3—7).

Хранит лемму, целевую основу Русидо, часть речи и морфологический тип.
Основы сохраняются явно, потому что надежное извлечение основы простым
удалением русских окончаний невозможно (книга → книг, дверь → двер,
армия → арми — README.md, 4.5).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

POS_NOUN = "noun"
POS_VERB = "verb"
POS_ADJ = "adj"
POS_PRON = "pronoun"
POS_NUM = "numeral"
POS_ADV = "adv"
POS_PARTICLE = "particle"
POS_CONJ = "conj"
POS_PREP = "prep"

# Типы основ существительных: гласная/согласная основа + мягкий знак.
STEM_VOWEL = "vowel"      # книг(а), стол(∅)...: основа на гласную или обычную согласную
STEM_PALATAL = "palatal"  # двер(ь): основа оканчивается на ь — показатель мягкости

# Типы основ глаголов для вставки соединительной гласной «е» (Rusido.md, 7.2).
VERB_VOWEL = "vowel_stem"     # чита-, дела-, люби-
VERB_CONSONANT = "cons_stem"  # ид- → идем, идеш...


@dataclass
class LexiconEntry:
    lemma: str
    stem: str
    pos: str
    stem_type: str = STEM_VOWEL
    source_form: str | None = None  # каноническая форма Русидо (инфинитив, -ий ...)
    ru_translation: str | None = None
    meta: dict = field(default_factory=dict)


def _n(lemma, stem, **kw):
    return LexiconEntry(lemma=lemma, stem=stem, pos=POS_NOUN, **kw)


def _v(lemma, stem, infinitive, stem_type=VERB_VOWEL):
    return LexiconEntry(lemma=lemma, stem=stem, pos=POS_VERB,
                        stem_type=stem_type, source_form=infinitive)


def _a(lemma, stem):
    return LexiconEntry(lemma=lemma, stem=stem, pos=POS_ADJ, source_form=stem + "ий")


DEFAULT_LEXICON: list[LexiconEntry] = [
    # --- Существительные (основа из Rusido.md, раздел 3) ---
    _n("стол", "стол"),
    _n("книга", "книг"),
    _n("дом", "дом"),
    _n("город", "город"),
    _n("собака", "собак"),
    _n("брат", "брат"),
    _n("человек", "человек"),
    _n("письмо", "письм"),
    _n("автор", "автор"),
    _n("язык", "язык"),
    _n("работа", "работ"),
    _n("дверь", "двер", stem_type=STEM_PALATAL),
    _n("армия", "арми"),
    _n("школа", "школ"),
    _n("вода", "вод"),
    _n("молоко", "молок"),
    _n("слово", "слов"),
    _n("окно", "окн"),
    _n("друг", "друг"),
    _n("имя", "имен"),
    # --- Глаголы (Rusido.md, 7.1—7.2) ---
    _v("читать", "чита", "читати"),
    _v("писать", "писа", "писати"),
    _v("делать", "дела", "делати"),
    _v("любить", "люби", "любити"),
    _v("говорить", "говори", "говорити"),
    _v("жить", "жи", "жити"),
    _v("идти", "ид", "ити", stem_type=VERB_CONSONANT),
    _v("работать", "работа", "работати"),
    _v("изучать", "изуча", "изучати"),
    _v("быть", "бу", "будти", stem_type=VERB_CONSONANT),
    _v("ходить", "хо", "ходити"),
    _v("мочь", "мож", "мочити", stem_type=VERB_CONSONANT),
    _v("знать", "зна", "знати"),
    _v("сказать", "ска", "сказати"),
    _v("приходить", "прихо", "приходити"),
    _v("прочитать", "проче", "прочитати"),
    _v("начинать", "нача", "начати"),
    _v("продолжать", "продолжа", "продолжати"),
    _v("строить", "стро", "строити"),
    # --- Прилагательные (Rusido.md, раздел 4) ---
    _a("новый", "нов"),
    _a("красивый", "красив"),
    _a("большой", "болш"),
    _a("интересный", "интерес"),
    _a("известный", "извест"),
    _a("русский", "руск"),
    _a("синий", "син"),
    _a("холодный", "холод"),
    _a("плохой", "плох"),
    _a("быстрый", "быстр"),
    # --- Местоимения (Rusido.md, 5.1—5.4) ---
    LexiconEntry("я", "я", POS_PRON, meta={"case": "nom", "person": 1, "number": "sg"}),
    LexiconEntry("ти", "ти", POS_PRON, meta={"case": "nom", "person": 2, "number": "sg"}),
    LexiconEntry("он", "он", POS_PRON, meta={"case": "nom", "person": 3, "number": "sg"}),
    LexiconEntry("ми", "ми", POS_PRON, meta={"case": "nom", "person": 1, "number": "pl"}),
    LexiconEntry("ви", "ви", POS_PRON, meta={"case": "nom", "person": 2, "number": "pl"}),
    LexiconEntry("они", "они", POS_PRON, meta={"case": "nom", "person": 3, "number": "pl"}),
    LexiconEntry("мне", "мне", POS_PRON, meta={"case": "obl", "person": 1, "number": "sg"}),
    LexiconEntry("тебе", "тебе", POS_PRON, meta={"case": "obl", "person": 2, "number": "sg"}),
    LexiconEntry("нему", "нему", POS_PRON, meta={"case": "obl", "person": 3, "number": "sg"}),
    LexiconEntry("нам", "нам", POS_PRON, meta={"case": "obl", "person": 1, "number": "pl"}),
    LexiconEntry("вам", "вам", POS_PRON, meta={"case": "obl", "person": 2, "number": "pl"}),
    LexiconEntry("ним", "ним", POS_PRON, meta={"case": "obl", "person": 3, "number": "pl"}),
    LexiconEntry("мой", "мой", POS_PRON, meta={"kind": "poss"}),
    LexiconEntry("твой", "твой", POS_PRON, meta={"kind": "poss"}),
    LexiconEntry("его", "его", POS_PRON, meta={"kind": "poss"}),
    LexiconEntry("наш", "наш", POS_PRON, meta={"kind": "poss"}),
    LexiconEntry("ваш", "ваш", POS_PRON, meta={"kind": "poss"}),
    LexiconEntry("их", "их", POS_PRON, meta={"kind": "poss"}),
    LexiconEntry("етот", "етот", POS_PRON, meta={"kind": "dem"}),
    LexiconEntry("тот", "тот", POS_PRON, meta={"kind": "dem"}),
    LexiconEntry("такой", "такой", POS_PRON, meta={"kind": "dem"}),
    LexiconEntry("се", "се", POS_PRON, meta={"kind": "refl-passive"}),
    # --- Числительные (Rusido.md, раздел 6) ---
    *[LexiconEntry(name, name, POS_NUM) for name in [
        "нол", "одн", "два", "три", "четир", "пят", "шест", "сем", "восем", "девят", "десят",
        "однадек", "дванадек", "тринадек", "четирнадек", "пятнадек",
        "шестнадек", "семнадек", "восемнадек", "девятнадек",
        "двадек", "тридек", "четирдек", "пятдек", "шестдек", "семдек", "восемдек", "девятдек",
        "сто", "двесто", "тристо", "четирсто", "пятсто",
        "однтис", "дватис", "тритис", "четиртис", "пяттис",
    ]],
    # --- Наречия, частицы, союзы, предлоги (Rusido.md, 8.6—8.8) ---
    LexiconEntry("уже", "уже", POS_ADV),
    LexiconEntry("ешо", "ешо", POS_ADV),
    LexiconEntry("только", "только", POS_PARTICLE),
    LexiconEntry("может", "может", POS_PARTICLE),
    LexiconEntry("да", "да", POS_PARTICLE),
    LexiconEntry("нет", "нет", POS_PARTICLE),
    LexiconEntry("би", "би", POS_PARTICLE),
    LexiconEntry("ли", "ли", POS_PARTICLE),
    LexiconEntry("не", "не", POS_PARTICLE),
    LexiconEntry("и", "и", POS_CONJ),
    LexiconEntry("или", "или", POS_CONJ),
    LexiconEntry("но", "но", POS_CONJ),
    LexiconEntry("а", "а", POS_CONJ),
    LexiconEntry("если", "если", POS_CONJ),
    LexiconEntry("когда", "когда", POS_CONJ),
    LexiconEntry("што", "што", POS_CONJ),
    LexiconEntry("в", "в", POS_PREP),
    LexiconEntry("на", "на", POS_PREP),
    LexiconEntry("у", "у", POS_PREP),
    LexiconEntry("к", "к", POS_PREP),
    LexiconEntry("из", "из", POS_PREP),
    LexiconEntry("от", "от", POS_PREP),
    LexiconEntry("с", "с", POS_PREP),
    LexiconEntry("без", "без", POS_PREP),
    LexiconEntry("для", "для", POS_PREP),
    LexiconEntry("о", "о", POS_PREP),
    LexiconEntry("од", "од", POS_PREP),
    # Служебные формы глагольной связки и безличного местоимения
    LexiconEntry("ест", "ест", POS_VERB, stem_type=VERB_CONSONANT,
                 source_form="ест", meta={"invariant": True}),
    LexiconEntry("ну", "ну", POS_PARTICLE, meta={"kind": "impersonal"}),
]


class Lexicon:
    """Лексикон Русидо: поиск по лемме, основе и словоформе."""

    def __init__(self, entries: list[LexiconEntry] | None = None):
        self._by_lemma: dict[str, LexiconEntry] = {}
        self._forms: dict[str, LexiconEntry] = {}
        for entry in entries if entries is not None else DEFAULT_LEXICON:
            self.add(entry)

    def add(self, entry: LexiconEntry) -> None:
        self._by_lemma.setdefault(entry.lemma, entry)

    def lookup(self, lemma: str) -> LexiconEntry | None:
        return self._by_lemma.get(lemma)

    def has(self, lemma: str) -> bool:
        return lemma in self._by_lemma

    def get_all_nouns(self) -> list[str]:
        return [e.lemma for e in self._by_lemma.values() if e.pos == POS_NOUN]

    def get_all_verbs(self) -> list[str]:
        return [e.lemma for e in self._by_lemma.values() if e.pos == POS_VERB]

    def stems(self, pos: str) -> list[str]:
        return sorted({e.stem for e in self._by_lemma.values() if e.pos == pos})

    def to_json(self) -> str:
        return json.dumps([asdict(e) for e in self._by_lemma.values()],
                          ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Lexicon":
        data = json.loads(text)
        lex = cls([])
        for item in data:
            lex.add(LexiconEntry(**item))
        return lex
