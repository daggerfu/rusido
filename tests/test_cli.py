"""Тесты CLI (rusido.cli): перевод и валидация из файла и в файл."""

import pytest

from rusido.cli import main


def test_translate_file_to_file(tmp_path):
    src = tmp_path / "in.txt"
    src.write_text("Я читаю книгу.\n", encoding="utf-8")
    out = tmp_path / "out.txt"
    assert main(["translate", "-i", str(src), "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == "Я читам книгу."


def test_translate_positional_source(tmp_path):
    src = tmp_path / "in.txt"
    src.write_text("книгу", encoding="utf-8")
    out = tmp_path / "out.txt"
    assert main(["translate", str(src), "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == "книгу"


def test_translate_stdin_stdout(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", type("S", (), {"read": lambda self: "книга"})())
    assert main(["translate"]) == 0
    assert capsys.readouterr().out == "книг\n"


def test_translate_no_nlp(tmp_path):
    src = tmp_path / "in.txt"
    src.write_text("читаю", encoding="utf-8")
    out = tmp_path / "out.txt"
    assert main(["translate", "-i", str(src), "-o", str(out), "--no-nlp"]) == 0
    # без NLP форма настоящего времени не переводится (эвристика MVP)
    assert out.read_text(encoding="utf-8") == "читаю"


def test_validate_valid_file(tmp_path, capsys):
    src = tmp_path / "ok.txt"
    src.write_text("Я читам книгу.", encoding="utf-8")
    assert main(["validate", str(src)]) == 0
    assert "валиден: да" in capsys.readouterr().out


def test_validate_invalid_exit_code_and_report(tmp_path, capsys):
    src = tmp_path / "bad.txt"
    src.write_text("Я читаю книгу.", encoding="utf-8")
    assert main(["validate", str(src)]) == 1
    report = capsys.readouterr().out
    assert "валиден: нет" in report
    assert "[R005]" in report


def test_validate_strict_warning(tmp_path, capsys):
    src = tmp_path / "warn.txt"
    src.write_text("Я читам книгу", encoding="utf-8")
    assert main(["validate", str(src), "--strict"]) == 0
    assert "[R017]" in capsys.readouterr().out


def test_validate_output_file(tmp_path):
    src = tmp_path / "ok.txt"
    src.write_text("Я читам книгу.", encoding="utf-8")
    out = tmp_path / "report.txt"
    assert main(["validate", "-i", str(src), "-o", str(out)]) == 0
    assert "ошибок: 0" in out.read_text(encoding="utf-8")


def test_translate_missing_file_errors(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main(["translate", "-i", str(tmp_path / "nope.txt")])
    assert "nope.txt" in str(exc.value.code)


def test_corpus_add_and_stats(tmp_path, capsys):
    db = str(tmp_path / "c.db")
    assert main(["corpus", "add", "--ru", "Я читаю книгу.",
                 "--rusido", "Я читам книгу.", "--db", db]) == 0
    assert main(["corpus", "add", "--ru", "Дом.", "--rusido",
                 "Доме.", "--db", db]) == 0
    assert main(["corpus", "stats", "--db", db]) == 0
    out = capsys.readouterr().out
    assert "предложений: 2" in out
    assert "валидных: 2" in out


def test_corpus_add_invalid_exit_code(tmp_path, capsys):
    db = str(tmp_path / "c.db")
    assert main(["corpus", "add", "--ru", "Я читаю книгу.",
                 "--rusido", "Я читаю книгу.", "--db", db]) == 1
    assert "валидно: нет" in capsys.readouterr().out


def test_corpus_search(tmp_path, capsys):
    db = str(tmp_path / "c.db")
    main(["corpus", "add", "--ru", "Я читаю книгу.",
          "--rusido", "Я читам книгу.", "--db", db])
    assert main(["corpus", "search", "читам", "--db", db]) == 0
    assert "Я читам книгу." in capsys.readouterr().out


def test_dictionary_list_filters(capsys):
    assert main(["dictionary", "list", "-p", "verb", "-a"]) == 0
    out = capsys.readouterr().out
    assert "идти" in out
    assert "infinitive: и" in out
    assert "показано: 2 из 2" in out


def test_dictionary_list_search_and_limit(capsys):
    assert main(["dictionary", "list", "-s", "книг", "-n", "1"]) == 0
    out = capsys.readouterr().out
    assert "книга" in out
    assert "показано: 1 из" in out


def test_dictionary_list_formats(tmp_path, capsys):
    assert main(["dictionary", "list", "-p", "prep", "--format", "md",
                 "-o", str(tmp_path / "prep.md")]) == 0
    text = (tmp_path / "prep.md").read_text(encoding="utf-8")
    assert text.startswith("# Лексикон Русидо")
    assert "| предлог |" in text

    assert main(["dictionary", "list", "-p", "prep", "--format", "json"]) == 0
    import json
    data = json.loads(capsys.readouterr().out)
    assert any(e["lemma"] == "под" for e in data)


def test_dictionary_export_markdown(tmp_path):
    out = tmp_path / "lex.md"
    assert main(["dictionary", "export", str(out), "--format", "md"]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# Лексикон Русидо")
    assert "| Лемма | Основа |" in text
    assert "алломорфы" in text.lower() or "Алломорфы" in text


def test_dictionary_import_export(tmp_path):
    db = str(tmp_path / "d.db")
    out = tmp_path / "dict.json"
    assert main(["dictionary", "import", "--db", db]) == 0
    assert main(["dictionary", "export", str(out), "--db", db]) == 0
    import json
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) > 100


def test_translate_prints_warnings_to_stderr(tmp_path, capsys):
    src = tmp_path / "in.txt"
    src.write_text("Я вижу партия.", encoding="utf-8")
    assert main(["translate", str(src)]) == 0
    captured = capsys.readouterr()
    assert "партия" in captured.err
