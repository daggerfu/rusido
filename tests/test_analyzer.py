"""Тесты морфологического анализатора Русидо (README.md, раздел 7.4)."""

from rusido import RusidoAnalyzer


def test_analyze_list():
    items = RusidoAnalyzer().analyze("Я читам книгу")
    assert [item.word for item in items] == ["я", "читам", "книгу"]
    assert all(item.valid for item in items)

    assert (items[0].pos, items[0].person) == ("pronoun", 1)
    assert (items[1].pos, items[1].tense, items[1].person) == \
        ("verb", "present", 1)
    assert (items[2].pos, items[2].number, items[2].case) == \
        ("noun", "singular", "accusative")
    assert items[2].morphemes == [("книг", "ROOT"), ("у", "ACCUSATIVE")]


def test_analyze_noun_plural_case():
    item = RusidoAnalyzer().analyze_word("книгиу")
    assert item.valid
    assert (item.pos, item.root, item.number, item.case) == \
        ("noun", "книг", "plural", "accusative")
    assert item.morphemes == [
        ("книг", "ROOT"), ("и", "PLURAL"), ("у", "ACCUSATIVE"),
    ]


def test_analyze_consonant_imperative():
    item = RusidoAnalyzer().analyze_word("идите")
    assert item.valid
    assert (item.pos, item.root, item.mood, item.number) == \
        ("verb", "ид", "imperative", "plural")


def test_analyze_verb_allomorphs():
    # Инфинитив использует основу «и-», остальные формы — «ид-» (§7.1.1).
    items = {i.word: i for i in RusidoAnalyzer().analyze(
        "ити идем идел иди идите")}
    assert (items["ити"].pos, items["ити"].root,
            items["ити"].mood) == ("verb", "и", "infinitive")
    assert items["идем"].root == "ид"
    assert items["идел"].root == "ид"
    assert items["иди"].root == "ид"
    assert items["идите"].root == "ид"


def test_analyze_empty_and_unknown():
    analyzer = RusidoAnalyzer()
    assert analyzer.analyze("") == []
    assert analyzer.analyze("   ") == []

    item = analyzer.analyze_word("борьба")
    assert not item.valid
    assert item.pos is None
    assert analyzer.analyze("борьба")[0].valid is False
