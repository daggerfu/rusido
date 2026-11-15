"""rusido — регулярный русский язык: движок перевода и валидации (MVP).

Публичный API (см. README.md, раздел 7):
    RusidoConfig, RusidoTranslator, RusidoValidator, RusidoAnalyzer, Lexicon
"""

from rusido.analyzer import AnalysisItem, RusidoAnalyzer
from rusido.config import RusidoConfig
from rusido.core.normalizer import normalize_word
from rusido.lexicon import Lexicon, LexiconEntry
from rusido.morphology import adjectives, nouns, numerals, verbs
from rusido.translation import RusidoTranslator
from rusido.validation import Diagnostic, RusidoValidator, ValidationReport

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "RusidoConfig",
    "RusidoTranslator",
    "RusidoValidator",
    "RusidoAnalyzer",
    "Lexicon",
    "LexiconEntry",
    "Diagnostic",
    "ValidationReport",
    "AnalysisItem",
    "normalize_word",
    "nouns",
    "verbs",
    "adjectives",
    "numerals",
]
