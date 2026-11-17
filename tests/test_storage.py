"""Тесты SQLite-хранилища (README.md §4.6)."""

import json

import pytest

from rusido import Lexicon
from rusido.lexicon.dictionary import LexiconEntry
from rusido.lexicon.storage import SqliteStorage


@pytest.fixture
def storage(tmp_path):
    s = SqliteStorage(tmp_path / "test.db")
    yield s
    s.close()


def test_schema_created(storage, tmp_path):
    assert (tmp_path / "test.db").exists()


def test_upsert_and_lookup(storage):
    entry = LexiconEntry(lemma="книга", stem="книг", pos="noun")
    wid = storage.upsert_word(entry)
    assert storage.lookup("книга")["stem"] == "книг"
    # повторный upsert обновляет, а не дублирует
    entry.meta["frequency"] = 5
    wid2 = storage.upsert_word(entry)
    assert wid2 == wid
    assert storage.lookup("книга")["frequency"] == 5


def test_lookup_missing(storage):
    assert storage.lookup("нетакого") is None


def test_import_lexicon(storage):
    n = storage.import_lexicon(Lexicon())
    assert n > 100
    assert storage.lookup("читать")["stem"] == "чита"


def test_export_lexicon_roundtrip(storage):
    storage.import_lexicon(Lexicon())
    lexicon = storage.export_lexicon()
    assert lexicon.has("книга")
    entry = lexicon.lookup("читать")
    assert entry.stem == "чита"
    assert entry.pos == "verb"


def test_allomorphs_roundtrip(storage):
    entry = LexiconEntry(
        lemma="идти", stem="ид", pos="verb", stem_type="cons_stem",
        allomorphs={"infinitive": "и", "present": "ид",
                    "past": "ид", "imperative": "ид"},
    )
    storage.upsert_word(entry)
    assert json.loads(storage.lookup("идти")["allomorphs"]) == entry.allomorphs

    restored = storage.export_lexicon().lookup("идти")
    assert restored.allomorphs == entry.allomorphs
    assert restored.stem_for("infinitive") == "и"


def test_add_and_search_corpus(storage):
    storage.add_sentence("Я читаю книгу.", "Я читам книгу.", valid=True)
    storage.add_sentence("Дом.", "Доме.", valid=None)
    assert storage.search_corpus("читам") == [("Я читаю книгу.", "Я читам книгу.")]
    # поиск регистронезависим, в т.ч. для кириллицы
    assert len(storage.search_corpus("читаю")) == 1
    assert len(storage.search_corpus("Дом")) == 1
    assert len(storage.search_corpus("дом")) == 1
    assert storage.search_corpus("неттакого") == []


def test_corpus_stats(storage):
    storage.add_sentence("А.", "А.", valid=True)
    storage.add_sentence("Б.", "Б.", valid=False)
    storage.add_sentence("В.", "В.", valid=None)
    stats = storage.corpus_stats()
    assert stats["sentences"] == 3
    assert stats["valid"] == 1
    assert stats["unchecked"] == 1
    assert stats["words"] == 0
