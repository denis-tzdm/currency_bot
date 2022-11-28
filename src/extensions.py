import telebot
import requests
import redis
import json
from datetime import datetime

import config as conf


class BadInput(Exception):
    pass


class APIError(Exception):
    pass


class CacheError(Exception):
    pass


class CacheManager:
    ready: bool  # кэш подключен и готов к работе

    def __init__(self) -> None:
        self.cache = redis.Redis(
            host=conf.CACHE_HOST,
            port=conf.CACHE_PORT,
            password=conf.CACHE_PASS
        )
        try:
            self.cache.client()
            self.ready = True
        except redis.exceptions.RedisError as e:
            self.ready = False
            if conf.DEBUG:  # в рабочем режиме не показываем
                raise CacheError(f'Проблема при работе с кэшем: {e}')

    def get(self, key: str) -> dict | None:
        cached = self.cache.get(key)
        if cached:
            return json.loads(cached)
        else:
            return None

    def set(self, key: str, cache_values: dict):
        return self.cache.set(key, json.dumps(cache_values))


class Converter:
    amount: float  # конвертируемое количество
    from_sym: str  # символьный код исходной валюты
    to_sym: str  # символьный код итоговой валюты
    r_amount: float  # сконвертированное количество
    cache: CacheManager  # объект для работы с кэшем

    def __init__(self, message: telebot.types.Message) -> None:
        self.amount = 0
        self.from_sym = ''
        self.to_sym = ''
        self.r_amount = 0
        self.message = message
        self.validate_input()
        self.cache = CacheManager()

    def get_key(self) -> str:
        """Возвращает ключ для кэширования данных"""
        return f'{self.from_sym}_{self.to_sym}'

    def validate_input(self) -> None:
        c_input = self.message.text.split(' ')

        if not any(
                [(len(c_input) == 4 and c_input[2].lower() == 'в'),
                 len(c_input) == 3]
        ):
            raise BadInput('Укажите три значения через пробел так:\n'
                           '<i>количество исходная_валюта итоговая_валюта</i>\n'
                           'или так:\n'
                           '<i>количество исходная_валюта <b>в</b> итоговая_валюта</i>')
        if len(c_input) == 3:
            c_amount, c_from, c_to = c_input
        else:
            c_amount, c_from, _, c_to = c_input

        if c_from == c_to:
            raise BadInput(f'Ковертация в {c_to} не требуется.')

        self.from_sym = Converter.find_sym(c_from)
        self.to_sym = Converter.find_sym(c_to)

        try:
            self.amount = float(c_amount)
        except ValueError:
            raise BadInput(f'Не могу сконвертировать {c_amount} {self.from_sym}')

    @staticmethod
    def find_sym(name: str) -> str:
        """Возвращает символьный код валюты по введённой строке"""
        name_lower = name.lower()
        for k, v in conf.CURRENCIES.items():
            if k == name_lower or v['root'] in name_lower:
                return k.upper()
        raise BadInput(f'Валюта "{name}" не поддерживается.')

    def convert(self) -> None:
        self.get_cached()
        if not self.r_amount:
            self.get_current()

    def get_cached(self) -> None:
        """Заполняет сконвертированное количество по курсу из кэша"""
        self.r_amount = 0
        if self.cache.ready:
            try:
                cache_obj = self.cache.get(self.get_key())
                if cache_obj:
                    delta = (datetime.utcnow() -
                             datetime.fromtimestamp(cache_obj['timestamp']))
                    if delta.total_seconds() < conf.CACHE_DUE:  # кэш актуален
                        rate = cache_obj['rate']
                        self.r_amount = round(self.amount * rate, 6)
            except redis.exceptions.RedisError as e:
                if conf.DEBUG:  # в рабочем режиме не показываем
                    raise CacheError(f'Проблема при работе с кэшем: {e}')

    def get_current(self) -> None:
        """Заполняет сконвертированное количество по данным API"""
        headers = {'apikey': conf.API_KEY}
        url = f'{conf.API_ENDPOINT}' \
              f'to={self.to_sym}' \
              f'&from={self.from_sym}' \
              f'&amount={self.amount}'
        try:
            r = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError as e:
            raise APIError(f'Ошибка соединения с API: {e}')

        try:
            r_obj = json.loads(r.text)
        except ValueError as e:
            raise APIError(f'Неожиданный ответ сервера: {e}')

        if r.status_code != 200:
            api_msg = ''
            error = r_obj['error'] if 'error' in r_obj.keys() else None
            if error:
                api_msg = error['message'] if 'message' in error.keys() else ''
            msg = f'{str(r.status_code)}\n{api_msg}'
            raise APIError(f'Ошибка запроса к API: {msg}{r_obj}')

        if not all(_ in r_obj.keys() for _ in ['success', 'result']):
            raise APIError(f'Ошибка получения значения через API\n{r_obj}')

        if r_obj['success']:
            if self.cache.ready:
                self.cache_current_rate(r_obj)
            self.r_amount = r_obj['result']
        else:
            raise APIError(f'Ошибка получения значения через API\n{r_obj}')

    def cache_current_rate(self, r_obj: dict) -> None:
        info = r_obj['info'] if 'info' in r_obj.keys() else None
        if info and 'rate' in info.keys():
            try:
                cache_values = {
                    'timestamp': datetime.utcnow().timestamp(),
                    'rate': info['rate']
                }
                self.cache.set(self.get_key(), cache_values)
            except redis.exceptions.RedisError as e:
                if conf.DEBUG:  # в рабочем режиме не показываем
                    raise CacheError(f'Проблема при работе с кэшем: {e}')
        else:  # если в ответе API нет нужных полей, то для отладки сообщим
            if conf.DEBUG:
                raise APIError(f'Ошибка получения значения через API\n{r_obj}')
