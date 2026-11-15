"""CLI Русидо (README.md, раздел 7.6): перевод и валидация текста.

Запуск из корня репозитория:
    PYTHONPATH=src python3 -m rusido.cli translate -i input.txt -o output.txt
    PYTHONPATH=src python3 -m rusido.cli validate text.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rusido import RusidoTranslator, RusidoValidator

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
                           "пунктуации, код R007)")

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

    p_di = sub.add_parser("dictionary", help="словарь (SQLite, §4.6)")
    di_sub = p_di.add_subparsers(dest="dict_command", required=True)
    d_ex = di_sub.add_parser("export", help="экспорт лексикона в JSON")
    d_ex.add_argument("output", help="выходной JSON-файл")
    d_ex.add_argument("--db", default=None, help="путь к базе SQLite")
    d_im = di_sub.add_parser("import", help="импорт лексикона в базу")
    d_im.add_argument("--db", default=None, help="путь к базе SQLite")
    return parser


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


def cmd_dictionary(args: argparse.Namespace) -> int:
    from rusido import Lexicon
    storage = _open_storage(args)
    try:
        if args.dict_command == "import":
            n = storage.import_lexicon(Lexicon())
            print(f"импортировано записей: {n}")
            return 0
        lexicon = storage.export_lexicon()
        _write_text(args.output, lexicon.to_json() + "\n")
        return 0
    finally:
        storage.close()


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
