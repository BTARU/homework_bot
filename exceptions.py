class TokenNotFound(Exception):
    """Ошибка вызываемая при отсутствии токенов."""

    pass


class FromDateFormatError(Exception):
    """Передано неверное значение даты для запроса API."""

    pass


class ApiResponseKeysError(Exception):
    """Отсутствуют ожидаемые ключи в ответе API."""

    pass


class UnexpectedHomeworkStatus(Exception):
    """Неверный статус домашней работы в ответе API."""

    pass


class HomeworkNameMissing(Exception):
    """Отсутствует имя домашней работы в ответе API."""

    pass


class PracticumAuthorizationFailed(Exception):
    """Ошибка авторизации при запросе к API Практикума."""

    pass


class ServiceUnavailable(Exception):
    """При запросе к API Практикума нет ответа от сервера."""

    pass
