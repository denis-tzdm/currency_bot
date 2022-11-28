DEBUG = False  # в режиме отладки бот выводит описание ошибок в чат
BOT_TOKEN = ''
API_ENDPOINT = 'https://api.apilayer.com/exchangerates_data/convert?'
API_KEY = ''
CACHE_HOST = ''  # redis database endpoint
CACHE_PORT = 12345
CACHE_PASS = ''
CACHE_DUE = 3600  # срок актуальности кэша в секундах
CURRENCIES = {
    'rub': {  # символьный код в нижнем регистре
        'name': 'Российский рубль',  # полное наименование
        'short': 'рубль',  # краткое наименование для пользователя
        'root': 'рубл'},  # корень слова для поиска
    'usd': {
        'name': 'Американский доллар',
        'short': 'доллар',
        'root': 'доллар'},
    'eur': {
        'name': 'Евро',
        'short': 'евро',
        'root': 'евро'},
    'gbp': {
        'name': 'Фунт стерлинга',
        'short': 'фунт',
        'root': 'фунт'},
    'cny': {
        'name': 'Китайский юань',
        'short': 'юань',
        'root': 'юан'},
    'jpy': {
        'name': 'Японская йена',
        'short': 'йена',
        'root': 'йен'},
    'try': {
        'name': 'Турецкая лира',
        'short': 'лира',
        'root': 'лир'},
    'amd': {
        'name': 'Армянский драм',
        'short': 'драм',
        'root': 'драм'},
    'ars': {
        'name': 'Аргентинское песо',
        'short': 'песо',
        'root': 'песо'},
}
