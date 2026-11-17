"""Лексикон Русидо (README.md, 4.5; Rusido.md, разделы 3—7).

Хранит лемму, целевую основу Русидо, часть речи и морфологический тип.
Основы сохраняются явно, потому что надежное извлечение основы простым
удалением русских окончаний невозможно (книга → книг, дверь → двер,
армия → арми — README.md, 4.5).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from rusido.core.normalizer import normalize_word
from rusido.exceptions import InvalidFeatureError

POS_NOUN = "noun"
POS_VERB = "verb"
POS_ADJ = "adj"
POS_PRON = "pronoun"
POS_NUM = "numeral"
POS_ADV = "adv"
POS_PARTICLE = "particle"
POS_CONJ = "conj"
POS_PREP = "prep"

# Русские названия частей речи для CLI и Markdown-экспорта.
POS_LABELS = {
    POS_NOUN: "существительное",
    POS_VERB: "глагол",
    POS_ADJ: "прилагательное",
    POS_PRON: "местоимение",
    POS_NUM: "числительное",
    POS_ADV: "наречие",
    POS_PARTICLE: "частица",
    POS_CONJ: "союз",
    POS_PREP: "предлог",
}

# Внешние словари: data/lexicon/*.json, формат — список LexiconEntry (README.md, 4.5).
EXTERNAL_LEXICON_DIR = Path(__file__).resolve().parents[3] / "data" / "lexicon"

# Типы основ существительных: гласная/согласная основа + мягкий знак.
STEM_VOWEL = "vowel"      # книг(а), стол(∅)...: основа на гласную или обычную согласную
STEM_PALATAL = "palatal"  # двер(ь): основа оканчивается на ь — показатель мягкости

# Типы основ глаголов для вставки соединительной гласной «е» (Rusido.md, 7.2).
VERB_VOWEL = "vowel_stem"     # чита-, дела-, люби-
VERB_CONSONANT = "cons_stem"  # ид- → идем, идеш...

# Алломорфы глагольной основы (Rusido.md, 7.1.1; D-015).
ALLO_INFINITIVE = "infinitive"
ALLO_PRESENT = "present"
ALLO_PAST = "past"
ALLO_IMPERATIVE = "imperative"
ALLOMORPH_KINDS = (ALLO_INFINITIVE, ALLO_PRESENT, ALLO_PAST, ALLO_IMPERATIVE)


@dataclass
class LexiconEntry:
    lemma: str
    stem: str
    pos: str
    stem_type: str = STEM_VOWEL
    source_form: str | None = None  # каноническая форма Русидо (инфинитив, -ий ...)
    ru_translation: str | None = None
    meta: dict = field(default_factory=dict)
    allomorphs: dict[str, str] = field(default_factory=dict)

    def stem_for(self, kind: str) -> str:
        """Основа для формы данного типа; по умолчанию — основная основа."""
        return self.allomorphs.get(kind, self.stem)

    def all_stems(self) -> set[str]:
        """Все основы записи, включая алломорфы (для разбора форм)."""
        return {self.stem, *self.allomorphs.values()}

    def set_allomorph(self, kind: str, stem: str) -> None:
        """Зафиксировать алломорф для одного из четырёх типов форм (D-015).

        Неизвестный тип формы отвергается: стабильный набор ALLOMORPH_KINDS
        используется переводчиком, валидатором и морфологическим анализатором.
        """
        if kind not in ALLOMORPH_KINDS:
            raise InvalidFeatureError(
                f"неизвестный тип алломорфа '{kind}'; допустимы: "
                f"{', '.join(ALLOMORPH_KINDS)}")
        self.allomorphs[kind] = normalize_word(stem)


def _md_cell(value: str) -> str:
    """Экранировать разделитель колонок Markdown-таблицы."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _n(lemma, stem, **kw):
    return LexiconEntry(lemma=lemma, stem=stem, pos=POS_NOUN, **kw)


def _v(lemma, stem, infinitive, stem_type=VERB_VOWEL, allomorphs=None):
    return LexiconEntry(lemma=lemma, stem=stem, pos=POS_VERB,
                        stem_type=stem_type, source_form=infinitive,
                        allomorphs=allomorphs or {})


def _a(lemma, stem):
    return LexiconEntry(lemma=lemma, stem=stem, pos=POS_ADJ, source_form=stem + "ий")


def _with_bootstrap(entries: list[LexiconEntry]) -> list[LexiconEntry]:
    """Дополнить лексикон bootstrap-записями (lexicon/bootstrap.py)."""
    from rusido.lexicon.bootstrap import bootstrap_entries  # noqa: PLC0415
    seen = {e.lemma for e in entries}
    for e in bootstrap_entries():
        if e.lemma not in seen:
            entries.append(e)
            seen.add(e.lemma)
    return entries


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
    _v("идти", "ид", "ити", stem_type=VERB_CONSONANT, allomorphs={
        ALLO_INFINITIVE: "и", ALLO_PRESENT: "ид",
        ALLO_PAST: "ид", ALLO_IMPERATIVE: "ид",
    }),
    _v("работать", "работа", "работати"),
    _v("изучать", "изуча", "изучати"),
    _v("быть", "буд", "будти", stem_type=VERB_CONSONANT),
    _v("ходить", "хо", "ходити"),
    _v("мочь", "мож", "мочити", stem_type=VERB_CONSONANT),
    _v("знать", "зна", "знати"),
    _v("сказать", "сказ", "сказати"),
    _v("приходить", "прихо", "приходити"),
    _v("прочитать", "прочита", "прочитати"),
    _v("начинать", "нача", "начати"),
    _v("продолжать", "продолжа", "продолжати"),
    _v("прийти", "прий", "прийти", stem_type=VERB_CONSONANT, allomorphs={
        ALLO_PAST: "приш", ALLO_IMPERATIVE: "прийд",
    }),
    _v("строить", "стро", "строити"),
    # --- Прилагательные (Rusido.md, раздел 4) ---
    _a("новый", "нов"),
    _a("красивый", "красив"),
    _a("большой", "болш"),
    _a("интересный", "интерес"),
    _a("известный", "извест"),
    _a("руский", "руск"),
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
        "нол", "одн", "два", "три", "четир", "пят", "шест", "сем", "восем", "девят",
        "десят", "однадек", "дванадек", "тринадек", "четирнадек", "пятнадек",
        "шестнадек", "семнадек", "восемнадек", "девятнадек",
        "двадек", "тридек", "четирдек", "пятдек", "шестдек", "семдек", "восемдек", "девятдек",
        "сто", "двасто", "тристо", "четирсто", "пятсто", "шестсто", "семсто",
        "восемсто", "девятсто", "однтис", "дватис", "тритис", "четиртис",
        "пятис", "шестис", "семтис", "восемтис", "девятис",
    ]],
    # --- Наречия, частицы, союзы, предлоги (Rusido.md, 8.6—8.8) ---
    LexiconEntry("уже", "уже", POS_ADV),
    LexiconEntry("бистро", "бистро", POS_ADV),
    LexiconEntry("бистрей", "бистрей", POS_ADV),
    LexiconEntry("бистрейш", "бистрейш", POS_ADV),
    LexiconEntry("холодно", "холодно", POS_ADV),
    LexiconEntry("плохо", "плохо", POS_ADV),
    LexiconEntry("более", "более", POS_ADV),
    LexiconEntry("самий", "самий", POS_ADV),
    LexiconEntry("вчера", "вчера", POS_ADV),
    LexiconEntry("завтра", "завтра", POS_ADV),
    LexiconEntry("сегодня", "сегодня", POS_ADV),
    LexiconEntry("сейчас", "сейчас", POS_ADV),
    LexiconEntry("вместе", "вместе", POS_ADV),
    LexiconEntry("здесь", "здесь", POS_ADV),
    LexiconEntry("там", "там", POS_ADV),
    LexiconEntry("домой", "домой", POS_ADV),
    LexiconEntry("ешо", "ешо", POS_ADV),
    LexiconEntry("только", "только", POS_PARTICLE),
    LexiconEntry("может", "может", POS_PARTICLE),
    LexiconEntry("да", "да", POS_PARTICLE),
    LexiconEntry("нет", "нет", POS_PARTICLE),
    LexiconEntry("би", "би", POS_PARTICLE),
    LexiconEntry("ли", "ли", POS_PARTICLE),
    LexiconEntry("не", "не", POS_PARTICLE),
    LexiconEntry("же", "же", POS_PARTICLE),  # §8.8: усилительная частица
    LexiconEntry("и", "и", POS_CONJ),
    LexiconEntry("или", "или", POS_CONJ),
    LexiconEntry("но", "но", POS_CONJ),
    LexiconEntry("а", "а", POS_CONJ),
    LexiconEntry("если", "если", POS_CONJ),
    LexiconEntry("когда", "когда", POS_CONJ),
    LexiconEntry("што", "што", POS_CONJ),
    LexiconEntry("штоби", "штоби", POS_CONJ),
    LexiconEntry("кторий", "кторий", POS_CONJ),
    LexiconEntry("также", "также", POS_CONJ),
    LexiconEntry("тоже", "тоже", POS_CONJ),
    LexiconEntry("однако", "однако", POS_CONJ),
    LexiconEntry("либо", "либо", POS_CONJ),
    LexiconEntry("так", "так", POS_CONJ),
    LexiconEntry("потому", "потому", POS_CONJ),
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
    # Вопросительные местоимения (Rusido.md, 5.5)
    LexiconEntry("кто", "кто", POS_PRON, meta={"kind": "interr"}),
    LexiconEntry("какий", "какий", POS_PRON, meta={"kind": "interr"}),
    LexiconEntry("где", "где", POS_PRON, meta={"kind": "interr"}),
    LexiconEntry("куда", "куда", POS_PRON, meta={"kind": "interr"}),
    LexiconEntry("откуда", "откуда", POS_PRON, meta={"kind": "interr"}),
    LexiconEntry("почему", "почему", POS_PRON, meta={"kind": "interr"}),
    LexiconEntry("как", "как", POS_PRON, meta={"kind": "interr"}),
    LexiconEntry("сколько", "сколько", POS_PRON, meta={"kind": "interr"}),
    LexiconEntry("под", "под", POS_PREP),  # §8.6: под столе
    LexiconEntry("до", "до", POS_PREP),    # §9.1: приставка до-, управление в CLI
    # Служебные формы глагольной связки и безличного местоимения
    LexiconEntry("ест", "ест", POS_VERB, stem_type=VERB_CONSONANT,
                 source_form="ест", meta={"invariant": True}),
    LexiconEntry("ну", "ну", POS_PARTICLE, meta={"kind": "impersonal"}),
    # Приветствия — инвариантные междометия (Rusido.md §9.3:
    # адаптированные слова включаются в словарь и не изменяются).
    LexiconEntry("привет", "привет", POS_PARTICLE, meta={"kind": "greeting"}),
    LexiconEntry("здравствуй", "здравствуй", POS_PARTICLE,
                 meta={"kind": "greeting"}),
    LexiconEntry("здравствуйте", "здравствуйте", POS_PARTICLE,
                 meta={"kind": "greeting"}),
]
DEFAULT_LEXICON = _with_bootstrap(DEFAULT_LEXICON)


def load_external_entries(directory: Path | None = None) -> list[LexiconEntry]:
    """Загрузить дополнительные записи из `data/lexicon/*.json`.

    Отсутствующий каталог — нормальная ситуация (пакет работает и без
    внешних словарей). Битый файл — ошибка конфигурации, её не скрываем.
    """
    folder = directory or EXTERNAL_LEXICON_DIR
    if not folder.is_dir():
        return []
    entries: list[LexiconEntry] = []
    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{path}: ожидается список записей лексикона")
        entries.extend(LexiconEntry(**item) for item in data)
    return entries


class Lexicon:
    """Лексикон Русидо: поиск по лемме, основе и словоформе."""

    def __init__(self, entries: list[LexiconEntry] | None = None,
                 load_external: bool = True):
        self._by_lemma: dict[str, LexiconEntry] = {}
        self._forms: dict[str, LexiconEntry] = {}
        if entries is None:
            entries = DEFAULT_LEXICON + (load_external_entries()
                                         if load_external else [])
        for entry in entries:
            self.add(entry)

    def __len__(self) -> int:
        """Число лексических записей (критерий MVP — README.md, §15)."""
        return len(self._by_lemma)

    def __contains__(self, lemma: str) -> bool:
        return lemma in self._by_lemma

    def add(self, entry: LexiconEntry) -> None:
        # Лемма, основа и каноническая форма хранятся в орфографии Русидо:
        # нормализация при добавлении (Rusido.md, 2.2 и 2.6).
        entry.lemma = normalize_word(entry.lemma)
        entry.stem = normalize_word(entry.stem)
        if entry.source_form is not None:
            entry.source_form = normalize_word(entry.source_form)
        if entry.allomorphs:
            unknown = set(entry.allomorphs) - set(ALLOMORPH_KINDS)
            if unknown:
                raise InvalidFeatureError(
                    f"неизвестные типы алломорфов: {', '.join(sorted(unknown))}")
            entry.allomorphs = {kind: normalize_word(stem)
                                for kind, stem in entry.allomorphs.items()}
        self._by_lemma.setdefault(entry.lemma, entry)
        if entry.source_form is not None:
            self._forms.setdefault(entry.source_form, entry)

    def lookup(self, lemma: str) -> LexiconEntry | None:
        return self._by_lemma.get(lemma)

    def lookup_form(self, form: str) -> LexiconEntry | None:
        """Найти запись по канонической словоформе Русидо (инфинитив, -ий...)."""
        return self._forms.get(normalize_word(form))

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

    def to_markdown(self) -> str:
        """Экспорт лексикона в Markdown-таблицу (CLI: dictionary export)."""
        lines = [
            "# Лексикон Русидо",
            "",
            f"Записей: {len(self)}",
            "",
            "| Лемма | Основа | Часть речи | Тип основы "
            "| Каноническая форма | Алломорфы | Перевод |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for e in self._by_lemma.values():
            allos = ", ".join(f"{k}: {v}" for k, v in e.allomorphs.items()) or "—"
            cells = [
                e.lemma, e.stem, POS_LABELS.get(e.pos, e.pos), e.stem_type,
                e.source_form or "—", allos, e.ru_translation or "—",
            ]
            lines.append("| " + " | ".join(_md_cell(c) for c in cells) + " |")
        return "\n".join(lines) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "Lexicon":
        data = json.loads(text)
        lex = cls([])
        for item in data:
            lex.add(LexiconEntry(**item))
        return lex
