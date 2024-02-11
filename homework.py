import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telegram import Bot, Message
from telegram.error import TelegramError

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():  # Согласовали не править(не пропускают тесты)
    """Проверка доступности необходимых переменных окружения."""
    for token in (TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID):
        if not token:
            logging.critical(
                ('Отсутствует обязательная переменная окружения.\n'
                 'Программа принудительно остановлена.')
            )
            sys.exit('Отсутствует обязательная переменная окружения')


def send_message(bot: Bot, message: str) -> Message:
    """Отправка сообщения ботом в телеграм о статусе работы."""
    try:
        logging.debug(f'Попытка отправки сообщения: "{message}"..')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug(f'Сообщение "{message}" успешно отправлено.')
    except TelegramError as error:
        logging.error(
            f'Ошибка при попытке отправить сообщение в Telegram: {error}'
        )
        raise exceptions.TelegramMessageError


def get_api_answer(timestamp: int) -> dict:
    """Запрос к API, приведение ответа к формату python."""
    try:
        logging.debug(f'Попытка запроса к API: {ENDPOINT} ..')
        response = requests.get(
            ENDPOINT,
            headers={'Authorization': f'OAuth {PRACTICUM_TOKEN}'},
            params={'from_date': timestamp}
        )
    except Exception:
        raise exceptions.ApiRequestError('Ошибка при попытке запроса к API')
    if response.status_code == 503:
        raise exceptions.ServiceUnavailableError(
            f'Эндпоинт {ENDPOINT} недоступен'
        )
    if response.status_code == 400:
        raise exceptions.FromDateFormatError(
            'Получено неверное значение ключа "from_date"'
        )
    elif response.status_code == 401:
        raise exceptions.PracticumAuthorizationError(
            'Учетные данные не были предоставлены'
        )
    elif response.status_code != 200:
        raise exceptions.UnexpectedResponseCodeError(
            'Ожидаемый код ответа API не равен 200'
        )
    return response.json()


def check_response(response):
    """Проверить ответ API на наличие обьекта homework."""
    if not isinstance(response, dict):
        raise TypeError('Полученный тип данных не равен dict')
    if 'homeworks' not in response:
        raise exceptions.ApiResponseKeysError(
            'Ключ homeworks отсутствует в ответе API'
        )
    if 'current_date' not in response:
        raise exceptions.ApiResponseKeysError(
            'Ключ current_date отсутствует в ответе API'
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError('Тип данных homeworks не равен list')


def parse_status(homework):
    """Извлекает из данных о конкретной домашней работе статус ее проверки."""
    status = homework.get('status')
    if not status:
        raise exceptions.HomeworkStatusKeyMissingError(
            'Отсутствует статус домашней работы в ответе API'
        )
    if status not in HOMEWORK_VERDICTS.keys():
        raise exceptions.HomeworkStatusError(
            'Ошибка при получении статуса работы.'
        )
    verdict = HOMEWORK_VERDICTS[status]
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise exceptions.HomeworkNameError(
            'Отсутствует имя домашней работы в ответе API.'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error_message: str = ''
    last_homework_status: str = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date')
            check_response(response)
            homeworks = response.get('homeworks')
            if homeworks:  # Если есть проверенная работа
                homework_status = parse_status(homeworks[0])
                if homework_status != last_homework_status:
                    send_message(bot, homework_status)
                    last_homework_status = homework_status
            else:
                logging.debug('Нет нового статуса проверки работы.')
        except exceptions.TelegramMessageError:
            pass
        except Exception as error:
            logging.error(error)
            error_message = f'Сбой в работе программы: {error}'
            if error_message != last_error_message:
                send_message(bot, error_message)
            last_error_message = error_message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        level=logging.DEBUG,
        stream=sys.stdout
    )
    main()
