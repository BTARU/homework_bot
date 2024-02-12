class FromDateFormatError(Exception):
    """Передано неверное значение даты для запроса API."""

    pass


class ApiRequestError(Exception):
    """Ошибка при попытке запроса к API."""

    pass


class UnexpectedResponseCodeError(Exception):
    """Ожидаемый код ответа API не равен 200."""

    pass


class ApiResponseKeysError(Exception):
    """Отсутствуют ожидаемые ключи в ответе API."""

    pass


class HomeworkStatusKeyMissingError(Exception):
    """Отсутствует статус домашней работы в ответе API."""

    pass


class HomeworkStatusError(Exception):
    """Неверный статус домашней работы в ответе API."""

    pass


class HomeworkNameError(Exception):
    """Отсутствует имя домашней работы в ответе API."""

    pass


class PracticumAuthorizationError(Exception):
    """Ошибка авторизации при запросе к API Практикума."""

    pass


class ServiceUnavailableError(Exception):
    """При запросе к API Практикума нет ответа от сервера."""

    pass


class TelegramMessageError(Exception):
    """Ошибка при попытке отправить сообщение в Telegram."""

    pass
