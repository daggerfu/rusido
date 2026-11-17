"""Тесты валидатора Русидо (README.md, разделы 3.2 и 9)."""

import pytest


def test_valid_sentence(validator):
    report = validator.validate("Я читам книгу.")
    assert report.valid
    assert not report.errors


def test_invalid_word_code_r005(validator):
    report = validator.validate("Я вижу ковер.")
    codes = [e.code for e in report.errors]
    assert "R005" in codes
    assert not report.valid


def test_unknown_word_has_suggestion(validator):
    # опечатка без удвоенных согласных → R005 с ближайшим словарным словом
    report = validator.validate("книгуу.")
    diag = next(e for e in report.errors if e.code == "R005")
    assert diag.suggestion


def test_forbidden_letter_r006(validator):
    report = validator.validate("ёлка.")
    diag = next(e for e in report.errors if e.code == "R006")
    assert diag.suggestion == "елка"


def test_doubled_consonant_r007(validator):
    # удвоенные согласные запрещены (Rusido.md, 2.6)
    report = validator.validate("русский дом.")
    diag = next(e for e in report.errors if e.code == "R007")
    assert "сс" in diag.message
    assert diag.suggestion == "руский"
    assert validator.validate("руский дом.").valid


def test_agreement_error_r001(validator):
    # ми (1 л., мн. ч.) + читам (1 л., ед. ч.) — несогласованность
    report = validator.validate("Ми читам книгу.")
    assert any(e.code == "R001" for e in report.errors)


def test_allomorph_verb_forms_valid(validator):
    # Инфинитивная основа «и-», остальные алломорфы «ид-» (Rusido.md, 7.1.1).
    for text in ("Я идем.", "Они идели.", "Иди.", "Идите.", "Я будем ити."):
        report = validator.validate(text)
        assert report.valid, (text, [(d.code, d.message) for d in report.errors])


def test_all_predicates_checked(validator):
    # Раньше break после первого глагола скрывал ошибки во второй части.
    report = validator.validate("Я читаш и читат.")
    diags = [d for d in report.errors if d.code == "R001"]
    assert len(diags) == 2
    assert "читаш" in diags[0].message
    assert "читат" in diags[1].message


def test_r006_continues_with_normalized_form(validator):
    # «ёлка» → «елка»: после R006 форма всё равно проверяется как лексема.
    report = validator.validate("ёлка.")
    codes = [d.code for d in report.errors]
    # «елка» есть в лексиконе, поэтому после R006 R005 не выдаётся.
    assert codes == ["R006"]
    # «чёрный» нормализуется в известное слово — R005 не нужен.
    assert [d.code for d in validator.validate("чёрный дом.").errors] == ["R006"]


def test_agreement_valid(validator):
    assert validator.validate("Ми читами книгу.").valid
    assert validator.validate("Я читам книгу.").valid
    assert validator.validate("Ти читаш книгу.").valid
    assert validator.validate("Они читани книгу.").valid


def test_verb_forms_validate(validator):
    for form in ("читати", "читал", "читали", "читай", "читайте",
                 "идем", "идеш", "идет", "иди"):
        assert validator.validate_word(form).valid, form


def test_consonant_imperative_plural_validates(validator):
    # ид + и + те: форма образуется генератором и должна разбираться валидатором
    assert validator.validate_word("идите").valid


def test_noun_forms_validate(validator):
    for form in ("книг", "книгу", "книги", "книгио", "дверь", "двери"):
        assert validator.validate_word(form).valid, form


def test_adjective_form_validates(validator):
    assert validator.validate_word("новий").valid


def test_service_words_validate(validator):
    for form in ("не", "и", "в", "на", "уже", "би"):
        assert validator.validate_word(form).valid, form


def test_numeral_number_rule_r015(validator):
    # «два» и больше требуют мн. ч. существительного (Rusido.md, 6.5)
    report = validator.validate("два книгу.")
    diag = next(e for e in report.errors if e.code == "R015")
    assert diag.suggestion == "книгиу"


def test_teen_numeral_number_rule_r015(validator):
    # «однадек» (11) тоже требует мн. ч. — форма должна попадать в R015.
    report = validator.validate("однадек книгу.")
    diag = next(e for e in report.errors if e.code == "R015")
    assert diag.suggestion == "книгиу"


def test_numeral_value_drives_agreement_r015(validator):
    # Полное значение составного числа, а не последний компонент (§6.5).
    assert validator.validate("нол столи.").valid
    assert validator.validate("двадек одн столи.").valid  # 21
    assert validator.validate("сто одн столи.").valid     # 101

    for text in ("нол стол.", "двадек одн стол.", "сто одн стол."):
        report = validator.validate(text)
        diag = next(e for e in report.errors if e.code == "R015")
        assert diag.suggestion == "столи", text


def test_adjective_placement_warning_r008(validator):
    report = validator.validate("новий идет.")
    assert report.valid  # предупреждение, не ошибка
    assert any(w.code == "R008" for w in report.warnings)


def test_strict_mode_warns_without_final_punctuation():
    from rusido import RusidoValidator
    validator = RusidoValidator(strict=True)
    report = validator.validate("Я читам книгу")
    assert any(w.code == "R017" for w in report.warnings)


def test_report_counters(validator):
    report = validator.validate("Я читам книгу.\nОни идет.")
    assert report.tokens == 5
    assert report.sentences == 2


def test_validate_word_lowercases(validator):
    assert validator.validate_word("Книгу").valid


def test_diagnostics_property(validator):
    report = validator.validate("ёлка.")
    assert len(report.diagnostics) == len(report.errors) + len(report.warnings)


def test_spec_sample_text_validates(validator):
    """Образец текста из Rusido.md §11 проходит валидацию без ошибок."""
    sample = (
        "Мой брат жит в болший красивий доме. "
        "У нему ест два собаки. "
        "Я любим читати новий книгиу. "
        "Вчера я прочитал интересний книгу, кторий се писал од известний авторо. "
        "Завтра я будем писати письмо."
    )
    report = validator.validate(sample)
    assert report.valid, [(e.code, e.message) for e in report.errors]


def test_diagnostics_carry_positions(validator):
    # Диагностики уровня предложения локализуются: line/column/start/end.
    report = validator.validate("Я читат книгу. два стол.")
    r001 = [d for d in report.errors if d.code == "R001"]
    assert len(r001) == 1
    assert r001[0].line == 1
    assert "читат" == "Я читат книгу. два стол."[r001[0].start:r001[0].end]
    assert r001[0].column == r001[0].start
    r015 = [d for d in report.errors if d.code == "R015"]
    assert len(r015) == 1
    # start покрывает весь числительный оборот, end — существительное
    assert "два стол" == "Я читат книгу. два стол."[r015[0].start:r015[0].end]
    assert "стол" == "Я читат книгу. два стол."[r015[0].column:r015[0].end]


def test_dative_noun_not_confused_with_verb_r001(validator):
    # Пример §3.5: «брате» — брат + -е (дат. п.), а не бра- + -те (2 л. мн.).
    report = validator.validate("Я давам книгу брате.")
    assert report.valid, [(d.code, d.message) for d in report.errors]
    assert not any(d.code == "R001" for d in report.errors)


@pytest.mark.parametrize("word", [
    "одним", "дваим", "триим", "четирим", "пятим",
    "стоим", "двадек триим", "сто двадек пятим", "девятим",
])
def test_ordinal_numerals_valid(validator, word):
    # Порядковые числительные образуются с помощью -им (Rusido.md, §6.6).
    report = validator.validate(word + ".")
    assert report.valid, [(d.code, d.message) for d in report.errors]


def test_ordinal_matches_generator(validator):
    from rusido.morphology.numerals import ordinal_number
    for n in (1, 4, 5, 21, 100, 125, 2000, 9999):
        text = ordinal_number(n)
        assert validator.validate(text + ".").valid, (n, text)


def test_agreement_is_scoped_to_sentence(validator):
    # Пунктуация (Rusido.md, §2.8) разделяет предложения: «я» из первой
    # части не должно попадать в согласование со сказуемым второй части.
    for text in ("Я читам. Он читат.", "Он говорил: «Я читам».",
                 "— Я читам.", "«Ти читаш?» — он читат."):
        report = validator.validate(text)
        assert report.valid, (text, [(d.code, d.message)
                                     for d in report.errors])
