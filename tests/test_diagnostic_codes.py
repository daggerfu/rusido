"""Тесты реестра диагностических кодов (README.md, §9)."""

from rusido.validation.codes import CODES, implemented_codes, reserved_codes


def test_codes_unique_and_contiguous():
    codes = list(CODES)
    assert len(codes) == len(set(codes)) == 18
    assert codes == [f"R{i:03d}" for i in range(1, 19)]


def test_registry_fields_filled():
    for item in CODES.values():
        assert item.category
        assert item.level
        assert item.title
        assert item.condition
        assert item.status in {"implemented", "reserved"}


def test_reserved_codes_formalized():
    # Ранее неиспользуемые коды получили точное условие, но не выдаются.
    assert reserved_codes() == {
        "R002", "R003", "R004", "R009", "R010",
        "R011", "R012", "R013", "R014", "R016",
    }
    assert implemented_codes() == {
        "R001", "R005", "R006", "R007", "R008", "R015", "R017", "R018",
    }
    assert "падежа кодируется R002" in CODES["R013"].condition


def test_r007_unambiguous(validator):
    # R007 — только удвоенная согласная; символ вне алфавита — R018.
    report = validator.validate("русский дом.")
    assert [d.code for d in report.errors] == ["R007"]

    report = validator.validate("дом@")
    assert [d.code for d in report.errors] == ["R018"]
