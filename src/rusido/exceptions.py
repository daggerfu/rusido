"""Исключения пакета rusido."""


class RusidoError(Exception):
    """Базовое исключение rusido."""


class UnknownLemmaError(RusidoError):
    """Лемма отсутствует в лексиконе."""


class InvalidFeatureError(RusidoError):
    """Запрошенная грамматическая категория недопустима для данной части речи."""
