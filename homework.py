import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

import exceptions

load_dotenv()

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout
)

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


def check_tokens():
    """Проверка доступности необходимых переменных окружения."""
    for token in (TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID):
        if not token:
            logging.critical(
                ('Отсутствует обязательная переменная окружения.\n'
                 'Программа принудительно остановлена.')
            )
            raise exceptions.TokenNotFound


def send_message(bot: Bot, message: str):
    """Отправка сообщения ботом в телеграм о статусе работы."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug(f'Сообщение "{message}" успешно отправлено.')
    except TelegramError as error:
        logging.error(error)


def get_api_answer(timestamp: int):
    """Запрос к API, приведение ответа к формату python."""
    try:
        response = requests.get(
            ENDPOINT,
            headers={'Authorization': f'OAuth {PRACTICUM_TOKEN}'},
            params={'from_date': timestamp}
        )
    except Exception as error:
        logging.error(error)
    if response.status_code == 503:
        raise exceptions.ServiceUnavailable(f'Эндпоинт {ENDPOINT} недоступен')
    if response.status_code == 400:
        raise exceptions.FromDateFormatError('Wrong from_date format')
    elif response.status_code == 401:
        raise exceptions.PracticumAuthorizationFailed(
            'Учетные данные не были предоставлены'
        )
    elif response.status_code != 200:
        raise Exception('Ожидаемый код ответа API не равен 200')
    return response.json()


def check_response(response):
    """Проверить ответ API на наличие обьекта homework."""
    if not isinstance(response, dict):
        raise TypeError('Полученный тип данных не равен dict')
    if 'homeworks' not in response:
        raise exceptions.ApiResponseKeysError(
            'Ключ homeworks отсутствует в ответе API'
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError('Тип данных homeworks не равен list')
    if not response['homeworks']:
        logging.debug('Нет нового статуса проверки работы.')
        return False  # Ждем новый запрос
    return True


def parse_status(homework):
    """Извлекает из данных о конкретной домашней работе статус ее проверки."""
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS.keys():
        raise exceptions.UnexpectedHomeworkStatus(
            'Ошибка при получении статуса работы.'
        )
    verdict = HOMEWORK_VERDICTS[status]
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise exceptions.HomeworkNameMissing(
            'Отсутствует имя домашней работы в ответе API.'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error_message: str = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date')
            if check_response(response):  # Если есть проверенная работа
                send_message(bot, parse_status(response.get('homeworks')[0]))
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            logging.error(error)
            error_message = f'Сбой в работе программы: {error}'
            if error_message != last_error_message:
                send_message(bot, error_message)
            last_error_message = error_message
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
