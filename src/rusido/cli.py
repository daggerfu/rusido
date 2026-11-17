"""CLI Русидо (README.md, раздел 7.6): перевод и валидация текста.

Запуск из корня репозитория:
    PYTHONPATH=src python3 -m rusido.cli translate -i input.txt -o output.txt
    PYTHONPATH=src python3 -m rusido.cli validate text.txt
    PYTHONPATH=src python3 -m rusido.cli dictionary list -p verb -a
    PYTHONPATH=src python3 -m rusido.cli dictionary export --format md -o lex.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rusido import Lexicon, RusidoTranslator, RusidoValidator

PROG = "rusido"


def _read_text(path: str | None) -> str:
    """Прочитать текст из файла либо из stdin."""
    if path in (None, "-"):
        return sys.stdin.read()
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"{PROG}: не могу прочитать '{path}': {e}") from e


def _write_text(path: str | None, text: str) -> None:
    """Записать текст в файл либо в stdout."""
    if path in (None, "-"):
        sys.stdout.write(text)
        if text and not text.endswith("\n"):
            sys.stdout.write("\n")
        return
    Path(path).write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Инструменты языка Русидо: перевод русский → Русидо "
                    "и валидация текста Русидо.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_tr = sub.add_parser("translate", help="перевести текст в Русидо")
    p_tr.add_argument("source", nargs="?", default=None,
                      help="входной файл (по умолчанию — stdin)")
    p_tr.add_argument("-i", "--input", dest="input_file", default=None,
                      help="входной файл (перекрывает позиционный аргумент)")
    p_tr.add_argument("-o", "--output", default=None,
                      help="выходной файл (по умолчанию — stdout)")
    p_tr.add_argument("--no-nlp", action="store_true",
                      help="не использовать pymorphy3, только эвристики MVP")

    p_va = sub.add_parser("validate", help="проверить текст Русидо")
    p_va.add_argument("source", nargs="?", default=None,
                      help="входной файл (по умолчанию — stdin)")
    p_va.add_argument("-i", "--input", dest="input_file", default=None,
                      help="входной файл (перекрывает позиционный аргумент)")
    p_va.add_argument("-o", "--output", default=None,
                      help="файл для отчёта (по умолчанию — stdout)")
    p_va.add_argument("--strict", action="store_true",
                      help="строгий режим (предупреждение без финальной "
                           "пунктуации, код R017)")

    p_co = sub.add_parser("corpus", help="параллельный корпус (SQLite, §4.6)")
    co_sub = p_co.add_subparsers(dest="corpus_command", required=True)
    c_add = co_sub.add_parser("add", help="добавить пару предложений")
    c_add.add_argument("--ru", required=True, help="русское предложение")
    c_add.add_argument("--rusido", required=True, help="перевод на Русидо")
    c_add.add_argument("--db", default=None, help="путь к базе SQLite")
    c_se = co_sub.add_parser("search", help="поиск по корпусу")
    c_se.add_argument("query", help="строка поиска")
    c_se.add_argument("--db", default=None, help="путь к базе SQLite")
    c_st = co_sub.add_parser("stats", help="статистика корпуса")
    c_st.add_argument("--db", default=None, help="путь к базе SQLite")

    p_di = sub.add_parser("dictionary", help="лексикон (§15; SQLite — §4.6)")
    di_sub = p_di.add_subparsers(dest="dict_command", required=True)

    d_li = di_sub.add_parser("list", help="показать лексикон с фильтрами")
    d_li.add_argument("-p", "--pos", action="append", default=None,
                      help="часть речи (noun, verb, adj...); можно повторять")
    d_li.add_argument("-a", "--allomorphs", action="store_true",
                      help="только записи с алломорфами")
    d_li.add_argument("-s", "--search", default=None,
                      help="подстрока в лемме, основе, форме или переводе")
    d_li.add_argument("-n", "--limit", type=int, default=50,
                      help="максимум строк (0 — все, по умолчанию 50)")
    d_li.add_argument("--format", choices=("text", "md", "json"), default="text",
                      help="формат вывода (по умолчанию text)")
    d_li.add_argument("-o", "--output", default="-",
                      help="выходной файл (по умолчанию stdout)")
    _add_lexicon_source(d_li)

    d_ex = di_sub.add_parser("export", help="экспорт лексикона")
    d_ex.add_argument("output", nargs="?", default="-",
                      help="выходной файл (по умолчанию stdout)")
    d_ex.add_argument("--format", choices=("json", "md"), default="json",
                      help="json (по умолчанию) или markdown")
    _add_lexicon_source(d_ex)

    d_im = di_sub.add_parser("import", help="импорт лексикона в базу")
    d_im.add_argument("--db", default=None, help="путь к базе SQLite")
    return parser


def _add_lexicon_source(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", choices=("builtin", "db"), default="builtin",
                        help="источник: встроенный лексикон (по умолчанию) "
                             "или база SQLite")
    parser.add_argument("--db", default=None, help="путь к базе SQLite")


def _open_storage(args) -> "SqliteStorage":
    from rusido.lexicon.storage import DEFAULT_DB_PATH, SqliteStorage
    return SqliteStorage(args.db or DEFAULT_DB_PATH)


def cmd_translate(args: argparse.Namespace) -> int:
    source = args.input_file or args.source
    translator = RusidoTranslator(use_nlp=not args.no_nlp)
    result = translator.translate(_read_text(source))
    _write_text(args.output, result.text)
    for warning in result.warnings:
        print(f"{PROG}: предупреждение: {warning}", file=sys.stderr)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    source = args.input_file or args.source
    validator = RusidoValidator(strict=args.strict)
    report = validator.validate(_read_text(source))
    lines = [
        f"валиден: {'да' if report.valid else 'нет'}",
        f"предложений: {report.sentences}",
        f"слов: {report.tokens}",
        f"ошибок: {len(report.errors)}",
        f"предупреждений: {len(report.warnings)}",
    ]
    for d in report.errors:
        lines.append(f"[{d.code}] {d.line}:{d.column} ошибка: {d.message}"
                     + (f" (вариант: {d.suggestion})" if d.suggestion else ""))
    for d in report.warnings:
        lines.append(f"[{d.code}] {d.line}:{d.column} предупреждение: {d.message}"
                     + (f" (вариант: {d.suggestion})" if d.suggestion else ""))
    _write_text(args.output, "\n".join(lines) + "\n")
    return 0 if report.valid else 1


def cmd_corpus(args: argparse.Namespace) -> int:
    from rusido import RusidoValidator
    storage = _open_storage(args)
    try:
        if args.corpus_command == "add":
            valid = RusidoValidator().validate(args.rusido).valid
            storage.add_sentence(args.ru, args.rusido, valid=valid)
            print(f"добавлено (валидно: {'да' if valid else 'нет'})")
            return 0 if valid else 1
        if args.corpus_command == "search":
            for source_ru, target in storage.search_corpus(args.query):
                print(f"{source_ru}\n  → {target}")
            return 0
        stats = storage.corpus_stats()
        print(f"предложений: {stats['sentences']}")
        print(f"валидных: {stats['valid']}")
        print(f"непроверенных: {stats['unchecked']}")
        print(f"слов в словаре: {stats['words']}")
        return 0
    finally:
        storage.close()


def _load_lexicon(args: argparse.Namespace) -> Lexicon:
    """Встроенный лексикон или база — в зависимости от --source."""
    if getattr(args, "source", "builtin") == "db":
        storage = _open_storage(args)
        try:
            return storage.export_lexicon()
        finally:
            storage.close()
    return Lexicon()


def _filter_entries(lexicon: Lexicon, args: argparse.Namespace):
    from rusido.lexicon.dictionary import POS_LABELS

    entries = list(lexicon._by_lemma.values())
    if args.pos:
        unknown = set(args.pos) - set(POS_LABELS)
        if unknown:
            raise SystemExit(f"{PROG}: неизвестная часть речи: "
                             f"{', '.join(sorted(unknown))}")
        entries = [e for e in entries if e.pos in args.pos]
    if args.allomorphs:
        entries = [e for e in entries if e.allomorphs]
    if args.search:
        query = args.search.casefold()
        entries = [e for e in entries if query in " ".join((
            e.lemma, e.stem, e.source_form or "", e.ru_translation or "",
            " ".join(e.allomorphs))).casefold()]
    return sorted(entries, key=lambda e: (e.pos, e.lemma))


def _render_list(entries, total: int, fmt: str) -> str:
    import json
    from dataclasses import asdict

    from rusido.lexicon.dictionary import POS_LABELS

    if fmt == "md":
        return Lexicon(entries).to_markdown()
    if fmt == "json":
        return json.dumps([asdict(e) for e in entries],
                          ensure_ascii=False, indent=2) + "\n"

    shown = [(
        e.lemma, e.stem, POS_LABELS.get(e.pos, e.pos),
        ", ".join(f"{k}: {v}" for k, v in e.allomorphs.items()) or "—",
    ) for e in entries]
    headers = ("ЛЕММА", "ОСНОВА", "ЧАСТЬ РЕЧИ", "АЛЛОМОРФЫ")
    widths = [max(len(headers[i]), *(len(row[i]) for row in shown))
              if shown else len(headers[i]) for i in range(len(headers))]
    lines = [f"показано: {len(shown)} из {total}"]
    lines.append("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    lines.append("  ".join("-" * w for w in widths))
    lines.extend("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))
                 for row in shown)
    return "\n".join(lines) + "\n"


def cmd_dictionary(args: argparse.Namespace) -> int:
    if args.dict_command == "import":
        storage = _open_storage(args)
        try:
            n = storage.import_lexicon(Lexicon())
            print(f"импортировано записей: {n}")
            return 0
        finally:
            storage.close()

    lexicon = _load_lexicon(args)
    if args.dict_command == "export":
        text = (lexicon.to_markdown() if args.format == "md"
                else lexicon.to_json() + "\n")
        _write_text(args.output, text)
        return 0

    entries = _filter_entries(lexicon, args)
    total = len(entries)
    if args.limit > 0:
        entries = entries[:args.limit]
    _write_text(args.output, _render_list(entries, total, args.format))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "translate":
        return cmd_translate(args)
    if args.command == "corpus":
        return cmd_corpus(args)
    if args.command == "dictionary":
        return cmd_dictionary(args)
    return cmd_validate(args)


if __name__ == "__main__":
    sys.exit(main())
