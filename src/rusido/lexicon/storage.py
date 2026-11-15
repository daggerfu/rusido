"""Хранение словаря и корпуса в SQLite (README.md, §4.6).

База `data/rusido.db` — единое хранилище слов, переводов и параллельного
корпуса; JSON-файлы лексикона остаются формой импорта/экспорта. Морфология
и валидатор от базы не зависят.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from rusido.lexicon.dictionary import Lexicon, LexiconEntry

_SCHEMA = """
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY,
    lemma_ru TEXT NOT NULL,
    lemma_rusido TEXT NOT NULL,
    stem TEXT NOT NULL,
    pos TEXT NOT NULL,
    stem_type TEXT,
    allomorphs TEXT,
    frequency INTEGER DEFAULT 0,
    grammar_version TEXT DEFAULT '1.0'
);

CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES words(id),
    source_form TEXT NOT NULL,
    target_form TEXT NOT NULL,
    context TEXT
);

CREATE TABLE IF NOT EXISTS corpus_sentences (
    id INTEGER PRIMARY KEY,
    source_ru TEXT NOT NULL,
    target_rusido TEXT NOT NULL,
    valid INTEGER,
    source TEXT
);

CREATE INDEX IF NOT EXISTS idx_words_lemma ON words(lemma_ru);
CREATE INDEX IF NOT EXISTS idx_translations_pair
    ON translations(source_form, target_form);
CREATE INDEX IF NOT EXISTS idx_corpus_source ON corpus_sentences(source_ru);
"""

DEFAULT_DB_PATH = Path("data") / "rusido.db"


class SqliteStorage:
    """SQLite-бэкенд: словарь (`words`, `translations`) и корпус."""

    def __init__(self, path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(path)
        if self.path.parent != Path(""):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ---------- словарь ----------

    def upsert_word(self, entry: LexiconEntry,
                    lemma_ru: str | None = None) -> int:
        """Добавить слово либо обновить существующее; вернуть id."""
        cur = self._conn.execute(
            "SELECT id FROM words WHERE lemma_rusido = ?", (entry.lemma,))
        row = cur.fetchone()
        params = (
            lemma_ru or entry.lemma, entry.lemma, entry.stem, entry.pos,
            entry.stem_type,
            json.dumps(entry.meta.get("allomorphs"), ensure_ascii=False)
            if entry.meta.get("allomorphs") else None,
            int(entry.meta.get("frequency", 0)),
            entry.meta.get("grammar_version", "1.0"),
        )
        if row:
            self._conn.execute(
                "UPDATE words SET lemma_ru=?, lemma_rusido=?, stem=?, pos=?,"
                " stem_type=?, allomorphs=?, frequency=?, grammar_version=?"
                " WHERE id=?", params + (row[0],))
            self._conn.commit()
            return row[0]
        cur = self._conn.execute(
            "INSERT INTO words (lemma_ru, lemma_rusido, stem, pos, stem_type,"
            " allomorphs, frequency, grammar_version)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)", params)
        self._conn.commit()
        return cur.lastrowid

    def import_lexicon(self, lexicon: Lexicon) -> int:
        """Загрузить все записи лексикона в базу; вернуть число записей."""
        n = 0
        for entry in lexicon._by_lemma.values():
            self.upsert_word(entry)
            n += 1
        return n

    def lookup(self, lemma_rusido: str) -> dict | None:
        cur = self._conn.execute(
            "SELECT * FROM words WHERE lemma_rusido = ?", (lemma_rusido,))
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

    # ---------- корпус ----------

    def add_sentence(self, source_ru: str, target_rusido: str,
                     valid: bool | None = None,
                     source: str = "manual") -> int:
        """Добавить пару предложений в параллельный корпус."""
        cur = self._conn.execute(
            "INSERT INTO corpus_sentences (source_ru, target_rusido, valid,"
            " source) VALUES (?, ?, ?, ?)",
            (source_ru, target_rusido,
             None if valid is None else int(valid), source))
        self._conn.commit()
        return cur.lastrowid

    def search_corpus(self, query: str) -> list[tuple[str, str]]:
        """Поиск пар по вхождению строки (регистронезависимо).

        Фильтрация выполняется в Python: SQLite LIKE и lower()
        регистронезависимы только для ASCII. Для больших корпусов
        предполагается полнотекстовый индекс (FTS5).
        """
        needle = query.casefold()
        cur = self._conn.execute(
            "SELECT source_ru, target_rusido FROM corpus_sentences"
            " ORDER BY id")
        return [(s, t) for s, t in cur.fetchall()
                if needle in s.casefold() or needle in t.casefold()]

    def corpus_stats(self) -> dict:
        cur = self._conn.execute(
            "SELECT COUNT(*), SUM(valid), SUM(CASE WHEN valid IS NULL"
            " THEN 1 ELSE 0 END) FROM corpus_sentences")
        total, valid, unchecked = cur.fetchone()
        cur = self._conn.execute("SELECT COUNT(*) FROM words")
        words = cur.fetchone()[0]
        return {
            "sentences": total or 0,
            "valid": valid or 0,
            "unchecked": unchecked or 0,
            "words": words,
        }

    def export_lexicon(self) -> Lexicon:
        """Собрать лексикон из базы (для roundtrip JSON → SQLite → Lexicon)."""
        entries = []
        cur = self._conn.execute(
            "SELECT lemma_rusido, stem, pos, stem_type, allomorphs,"
            " frequency FROM words ORDER BY id")
        for lemma, stem, pos, stem_type, allomorphs, frequency in cur:
            meta = {}
            if allomorphs:
                meta["allomorphs"] = json.loads(allomorphs)
            if frequency:
                meta["frequency"] = frequency
            entries.append(LexiconEntry(lemma=lemma, stem=stem, pos=pos,
                                        stem_type=stem_type or "vowel",
                                        meta=meta))
        return Lexicon(entries)


def asdict_entry(entry: LexiconEntry) -> dict:
    """Сериализация записи лексикона в dict (для экспорта JSON)."""
    return asdict(entry)
