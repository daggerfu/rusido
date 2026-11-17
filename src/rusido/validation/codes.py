"""Реестр стабильных диагностических кодов валидатора (README.md, §9).

Каждый код описан ровно один раз: категория, уровень проверки, точное
условие выдачи и статус. Коды, для которых проверка ещё не реализована,
помечены как `reserved` — они не выдаются, но их смысл зафиксирован и не
может быть переиспользован под другую ошибку.
"""

from __future__ import annotations

from dataclasses import dataclass

ORTHOGRAPHY = "Orthography"
LEXICON = "Lexicon"
MORPHOLOGY = "Morphology"
SYNTAX = "Syntax"
NUMERALS = "Numerals"
GRAMMAR = "Grammar"

IMPLEMENTED = "implemented"
RESERVED = "reserved"


@dataclass(frozen=True)
class DiagnosticCode:
    code: str
    category: str
    level: str
    title: str
    condition: str
    status: str = RESERVED


def _c(code, category, level, title, condition, status=RESERVED):
    return DiagnosticCode(code, category, level, title, condition, status)


# Порядок совпадает с README.md §9; коды уникальны и непрерывны (R001…R018).
CODES: dict[str, DiagnosticCode] = {
    item.code: item for item in [
        _c("R001", SYNTAX, "syntax", "Неверное согласование глагола с субъектом",
           "личное местоимение-субъект и финитный глагол present/future "
           "имеют разные лицо или число", IMPLEMENTED),
        _c("R002", MORPHOLOGY, "morphology", "Неверный падеж",
           "падежный суффикс существительного не совпадает с падежом, "
           "требуемым предлогом (§8.6)"),
        _c("R003", MORPHOLOGY, "morphology", "Неверное число",
           "показатель числа существительного противоречит числу "
           "согласованного местоимения, при этом лицо совпадает"),
        _c("R004", MORPHOLOGY, "morphology", "Неверная форма глагола",
           "глагольная лексема найдена, но словоформа не разбирается "
           "ни одной парадигмой §7.2—7.7"),
        _c("R005", LEXICON, "lexicon", "Неизвестное слово",
           "слово не является леммой, канонической формой и не выводится "
           "морфологией из известной основы", IMPLEMENTED),
        _c("R006", ORTHOGRAPHY, "orthography", "Запрещённая буква",
           "в исходном написании есть ё/ы/э/ъ или иная буква вне алфавита "
           "с известной заменой (§2.4—2.5)", IMPLEMENTED),
        _c("R007", ORTHOGRAPHY, "orthography", "Некорректное написание",
           "удвоенная согласная в слове (§2.6); исправление — "
           "normalize_word", IMPLEMENTED),
        _c("R008", SYNTAX, "syntax", "Некорректная именная группа",
           "прилагательное на -ий не предшествует существительному (§8.2)",
           IMPLEMENTED),
        _c("R009", SYNTAX, "syntax", "Некорректная глагольная конструкция",
           "нарушена цепочка вспомогательный/условный/отрицание "
           "(§7.4, §7.6, §7.7)"),
        _c("R010", SYNTAX, "syntax", "Нарушение обязательного порядка",
           "порядок SVO или позиция определителя нарушены (§8.1—8.2)"),
        _c("R011", LEXICON, "lexicon", "Неверная лексическая основа",
           "форма разлагается на корень, отсутствующий в лексиконе"),
        _c("R012", MORPHOLOGY, "morphology", "Неправильный порядок морфем",
           "известные морфемы идут не в порядке ROOT+NUMBER+CASE (§3)"),
        _c("R013", SYNTAX, "syntax", "Некорректная конструкция с предлогом",
           "предлог не имеет следующего именного компонента (§8.6); "
           "несовпадение падежа кодируется R002"),
        _c("R014", MORPHOLOGY, "morphology", "Неизвестная форма словоизменения",
           "корень известен, но комбинация суффиксов отсутствует "
           "в грамматическом профиле"),
        _c("R015", NUMERALS, "syntax", "Нарушение правила числа после числительного",
           "полное числовое значение (0, 2+) не совпадает с числом "
           "существительного (§6.5)", IMPLEMENTED),
        _c("R016", GRAMMAR, "grammar", "Неизвестная грамматическая конструкция",
           "последовательность не соответствует ни одному правилу "
           "data/grammar/grammar.yaml"),
        _c("R017", ORTHOGRAPHY, "orthography", "Отсутствует финальная пунктуация",
           "strict-режим: текст не заканчивается на . ! ?", IMPLEMENTED),
        _c("R018", ORTHOGRAPHY, "orthography", "Символ вне алфавита",
           "после R006 в слове остался символ вне алфавита §2.1; "
           "выделено из R007, чтобы не смешивать два значения", IMPLEMENTED),
    ]
}

# Обратная совместимость: импорт по имени кода без словаря.
for _item in CODES.values():
    globals()[_item.code] = _item
del _item


def implemented_codes() -> set[str]:
    return {c for c, item in CODES.items() if item.status == IMPLEMENTED}


def reserved_codes() -> set[str]:
    return {c for c, item in CODES.items() if item.status == RESERVED}
