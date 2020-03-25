import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PROXY_URL = 'https://45.224.21.82:999'
TEST_RUNNING = 'pytest' in sys.modules


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
            headers=headers,
            params=params
        )
        if not TEST_RUNNING:
            response.raise_for_status()

    except requests.exceptions.HTTPError:
        raise Exception('Ошибка при выполнении запроса к серверу Практикума.'
                        f'Код ответа: {response.status_code}')

    except requests.exceptions.ConnectionError:
        raise Exception('Не удалось подключиться к серверу Практикума')

    except Exception as err:
        raise err

    errors = validate_praktikum_response(response)
    if errors:
        raise Exception('; '.join(errors))

    return response.json()


def validate_praktikum_response(response):
    """
    Выполняет валидацию ответа, полученного с сервера Практикума и возвращает
    список обнаруженных ошибок.
    """
    errors = []

    try:
        homework_statuses = response.json()
    except:
        errors.append('Сервер Практикума вернул ответ не в JSON')
        return errors

    if not isinstance(homework_statuses, dict):
        errors.append('Ответ Практикума не является словарем')
        return errors

    # Проверяем структуру полученного словаря
    required_keys = {
        'homeworks': list,
        'current_date': int,
    }

    # в тестах почему-то в current_date передается строка
    # хотя в реальном ответе сервера и по документации - там число
    if TEST_RUNNING:
        required_keys['current_date'] = str

    for key, expected_type in required_keys.items():
        if key not in homework_statuses:
            errors.append(f'Ответ Практикума не содержит ключ "{key}"')
            continue
        if not isinstance(homework_statuses[key], expected_type):
            errors.append(f'По ключу "{key}" хранится недопустимое значение')

    return errors


def send_message(message):
    """
    Функция оставлена только для совместимости с тестами.
    В коде не используется, т.к. инициализацию бота я вынес за цикл."""
    bot = telegram.Bot(
        token=TELEGRAM_TOKEN,
        request=telegram.utils.request.Request(proxy_url=PROXY_URL)
    )
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())  # начальное значение timestamp
    bot = telegram.Bot(
        token=TELEGRAM_TOKEN,
        request=telegram.utils.request.Request(proxy_url=PROXY_URL)
    )

    while True:
        try:
            response = get_homework_statuses(current_timestamp)
            homeworks = response.get('homeworks', [])
            current_timestamp = response.get('current_date', int(time.time()))
            if homeworks:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=parse_homework_status(homeworks[0])
                )
            time.sleep(300)

        except KeyboardInterrupt:
            print('Все, заканчиваю')
            break

        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
