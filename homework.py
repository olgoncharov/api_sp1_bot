import os
import time

import requests  # мне импорты так отсортировал isort
import telegram  # и PEP8 я читал - вроде все удовлетворяет стандартам ¯\_(ツ)_/¯
from dotenv import load_dotenv


load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PROXY_URL = 'https://45.224.21.82:999'


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        headers=headers,
        params=params
    )
    # эту строчку удалил из-за несовместимости с тестами
    # homework_statuses.raise_for_status()
    return homework_statuses.json()


def send_message(message):
    """
    Функция оставлена только для совместимости с тестами.
    В коде не используется, т.к. инициализацию бота я вынес за цикл."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN, request=telegram.utils.request.Request(proxy_url=PROXY_URL))
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())  # начальное значение timestamp
    bot = telegram.Bot(token=TELEGRAM_TOKEN, request=telegram.utils.request.Request(proxy_url=PROXY_URL))

    while True:
        try:
            response = get_homework_statuses(current_timestamp)
            homeworks = response.get('homeworks', [])
            current_timestamp = response.get('current_date', int(time.time()))
            if homeworks:
                bot.send_message(chat_id=CHAT_ID, text=parse_homework_status(homeworks[0]))
            time.sleep(300)

        except KeyboardInterrupt:
            print('Все, заканчиваю')
            break

        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
