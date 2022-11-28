import telebot

import config as conf
from extensions import Converter, BadInput, APIError, CacheError

bot = telebot.TeleBot(conf.BOT_TOKEN)


@bot.message_handler(commands=['start', 'help'])
def show_help(message: telebot.types.Message) -> None:
    r_message = 'Я умею конвертировать валюты.\n\n' \
                'Просто напишите\n' \
                '<i>сколько_конвертируем из_какой_валюты в_какую_валюту</i>.\n\n' \
                'Например,\n' \
                '<i>10 доллар рубль</i> сконвертирует 10 долларов в рубли.\n\n' \
                'Можно писать так:\n' \
                '<i>10 USD RUB</i>\n' \
                '…и так:\n' \
                '<i>10 доллар RUB</i>, <i>10 USD рубли</i>\n' \
                '…и даже так:\n' \
                '<i>10 долларов в рубли</i>\n' \
                'Команды:\n' \
                '/values — список доступных валют.'
    bot.send_message(message.chat.id, r_message, parse_mode='html')


@bot.message_handler(commands=['values'])
def show_currencies(message: telebot.types.Message) -> None:
    r_message = ''.join(f'- {v["short"]}, {k.upper()}: {v["name"]}\n'
                        for k, v in conf.CURRENCIES.items())
    bot.send_message(message.chat.id, f'Доступные валюты:\n{r_message}')


@bot.message_handler(content_types=['text'])
def show_rates(message: telebot.types.Message) -> None:
    try:
        converter = Converter(message)
        converter.convert()
    except BadInput as e:
        bot.send_message(message.chat.id, str(e), parse_mode='html')
    except APIError as e:
        msg = 'Что-то пошло не так, попробуйте позже :-('
        if conf.DEBUG:
            msg += '\n' + str(e)
        bot.send_message(message.chat.id, msg, parse_mode='html')
    except CacheError as e:
        if conf.DEBUG:
            bot.send_message(message.chat.id, str(e), parse_mode='html')
    else:
        r_message = f'{converter.amount} {converter.from_sym} ' \
                    f'это <b>{converter.r_amount}</b> {converter.to_sym}'
        bot.send_message(message.chat.id, r_message, parse_mode='html')


bot.polling(none_stop=True)
