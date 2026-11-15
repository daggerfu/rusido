# AGENTS.md — РУСИДО Tools

Файл для ИИ-агентов, работающих с этим репозиторием.

## Обзор проекта

**РУСИДО Tools** (`rusido-tools`, импортируемое имя `rusido`) — Python-пакет для работы с искусственным языком **Русидо**: регулярным русским языком с агглютинативной грамматикой (одно правило → один результат, без исключений). Два основных компонента:

1. **Переводчик** (`RusidoTranslator`): русский → Русидо.
2. **Валидатор** (`RusidoValidator`): проверка текста Русидо по уровням (орфография → лексика → морфология → синтаксис), диагностика со стабильными кодами ошибок R001—R016.

Дополнительно: морфологический анализатор (`RusidoAnalyzer`), лексикон (`Lexicon`), CLI `rusido`.

Проект находится на стадии **MVP**: переводчик использует **pymorphy3** (опционально, `rusido/core/nlp.py`) для разбора русских форм — лемма, падеж, число, лицо, время; при отсутствии библиотеки или выключенном флаге `use_nlp=False` работают собственные эвристики MVP. spaCy/NLTK не используются. Неизвестные слова орфографически нормализуются и снижают confidence. Есть `pyproject.toml` (установка `pip install -e .`, команда `rusido`); `Makefile` и `examples/` пока нет. CLI-модуль — `src/rusido/cli.py` (`translate`, `validate`, `corpus`, `dictionary`). SQLite-хранилище — `src/rusido/lexicon/storage.py` (`data/rusido.db` в .gitignore); YAML-грамматика — `data/grammar/grammar.yaml`. Базовый набор pytest-тестов есть в `tests/`.

## Документация проекта

- `README.md` — полная архитектурная концепция (архитектура, стек, API, CLI, коды ошибок, план этапов 1–4). Код ссылается на его разделы в docstring'ах.
- `docs/decisions.md` — журнал решений по языку (ADR-стиль, D-001…D-012): спорные вопросы спецификации закрыты там, новые решения фиксируются там же с привязкой к версии грамматики.
- `Rusido.md` — полная спецификация самого языка Русидо (алфавит, морфология, синтаксис). Код ссылается на её разделы.

Грамматика языка (корневая формула `ROOT + NUMBER + CASE`):
- Существительные: ед. ∅ / мн. `-и`; падежи: им. ∅, вин. `-у`, род. `-о`, дат. `-е`.
- Глаголы: инфинитив `-ти`; наст. ед. `-м -ш -т`, мн. `-ми -те -ни`; при согласной основе вставляется соединительная гласная `е` (ид- + е + м = идем); прош. ед. `-л` / мн. `-ли`; будущее — формы `будти` (будем, будеш, будет, будеми, будете, будени); условное: `би` + прош.; отрицание: `не`.
- Прилагательные: основа + `-ий`, неизменяемые, стоят перед существительным.
- Алфавит: 29 букв без `ё ы э ъ` (нормализация: ё→е, ы→и, э→е, ъ→ь; удвоенные согласные сокращаются, Rusido.md §2.6). Леммы и основы в лексиконе хранятся уже нормализованными (`Lexicon.add` нормализует при добавлении).
- Порядок слов SVO; синтаксис без грамматического рода.

## Структура кода

Исходники в `src/rusido/` (layout src-пакета, пока без packaging-файлов):

| Модуль | Назначение |
| --- | --- |
| `config.py` | `RusidoConfig` (grammar_version, analysis_backend, use_nlp, strict) |
| `exceptions.py` | `RusidoError`, `UnknownLemmaError`, `InvalidFeatureError` |
| `analyzer.py` | `RusidoAnalyzer`, `AnalysisItem` — морфемный разбор формы Русидо |
| `core/normalizer.py` | алфавит, запрещённые буквы, `normalize_word` |
| `core/nlp.py` | `RussianMorphAnalyzer`, `RussianAnalysis` — разбор русских форм через pymorphy3 (опционально, откат на эвристики) |
| `core/grammar.py` | `GrammarProfile`, `load_grammar` — загрузка формальной грамматики из `data/grammar/grammar.yaml` (тест `test_grammar_yaml` держит YAML и код синхронно) |
| `lexicon/dictionary.py` | `Lexicon`, `LexiconEntry`, константы POS и типов основ (STEM_VOWEL/STEM_PALATAL, VERB_VOWEL/VERB_CONSONANT); загрузка/экспорт JSON; 535+ записей (bootstrap из `lexicon/bootstrap.py`) |
| `morphology/nouns.py` | `inflect_noun`, константы числа/падежа |
| `morphology/verbs.py` | спряжение, будущее, повелительное, условное |
| `morphology/adjectives.py` | `build_adjective`, сравнительные степени (`более X` / `самий X`) |
| `morphology/numerals.py` | местоимения и числительные (кардинальные, порядковые `-им`) |
| `translation/translator.py` | `RusidoTranslator`, `TranslationResult`; таблица RU_TO_LEMMA_OVERRIDES |
| `validation/validator.py` | `RusidoValidator`, `ValidationReport`, `Diagnostic`; таблицы согласования глагола с субъектом |
| `cli.py` | CLI `rusido`: `translate` и `validate` с файлами/stdin/stdout (`python3 -m rusido.cli`) |

Ключевой принцип: переводчик и валидатор используют одни и те же морфологические правила и лексикон (`rusido.morphology`, `rusido.lexicon`).

## Соглашения по стилю

- **Язык — русский**: все docstring'и, комментарии и идентификаторы-множества на русском. Новый код должен следовать этому.
- `from __future__ import annotations`, типы в современном синтаксисе (`str | None`), dataclasses для моделей данных.
- Кодовые константы (суффиксы, таблицы спряжения, коды ошибок) оформляются как модульные константы, а не зашиваются в логику.
- Ссылки на источник правил в docstring'ах: `(README.md, раздел N)` / `(Rusido.md, раздел N)` — сохраняйте этот формат.
- Ошибки — через исключения из `rusido.exceptions`, диагностика валидатора — только со стабильными кодами R001—R016 (см. README.md §9).

## Сборка, тестирование, запуск

- Установка: `pip install -e .` из корня (зависимости: pymorphy3; extras: `spacy`, `evaluation`, `dev`). После установки доступна команда `rusido`; без установки запуск через `PYTHONPATH=src python3 -m rusido.cli`.
- Запуск из корня репозитория требует `PYTHONPATH=src`, например:
  - `PYTHONPATH=src python -c "from rusido import RusidoTranslator, RusidoValidator; t = RusidoTranslator(); print(t.translate('Я читаю книгу.').text)"`
  - `PYTHONPATH=src python -c "from rusido import RusidoValidator; print(RusidoValidator().validate('Я читам книгу.').valid)"`
- Тесты (`pytest`) находятся в `tests/` (запуск: `python3 -m pytest tests` из корня; `conftest.py` подставляет `src/` в `sys.path`). Покрытие: нормализатор, морфология (существительные, глаголы, прилагательные, числительные, `segment_noun`/`segment_verb`), переводчик, валидатор (коды R001/R005/R006/R007/R008/R015), сквозной тест «вывод переводчика проходит валидацию» (README.md §11). Тесты фиксируют текущее MVP-поведение; при доработке эвристик переводчика их нужно пересматривать. Добавляйте новые тесты туда же по мере развития кода.
- Требуемый Python по концепции — 3.11+.

## Дорожная карта (README.md §14)

1. Rusido Core (реализован в базовом виде), 2. Validator (базово реализован), 3. Translator (базово реализован, с NLP через pymorphy3), 4. CLI (базово реализован: `src/rusido/cli.py`) и Evaluation (не начат). Открытые вопросы спецификации — в TODO.md (README.md §13: будущее время, повелительное наклонение, местоимения, основы слов).

## Замечания по репозиторию

- В репозитории присутствуют `.DS_Store` — не коммитьте новые; в `.gitignore` они уже учтены.
- Русский текст в репозитории должен оставаться в кодировке UTF-8.
