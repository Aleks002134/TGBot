# требуемые библиотеки
# noinspection PyPackageRequirements
import requests
# noinspection PyPackageRequirements
import telebot
import time
import os
# noinspection PyPackageRequirements
from binance.exceptions import BinanceRequestException
# noinspection PyPackageRequirements
from binance.exceptions import BinanceAPIException
# noinspection PyPackageRequirements
from binance.client import Client
# noinspection PyPackageRequirements
from dotenv import load_dotenv
from io import StringIO  # требование для парсера LXML, он работает со строками асинхронно как с файлами
# noinspection PyPackageRequirements
from lxml import etree  # базовый модуль парсера


# добавляем токены бинанса для доступа к API
dotenv_path = os.path.join(os.path.dirname(__file__), 'tokens.env')
try:
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
except IOError:
    print('Путь или файл не существует')


# передаём данные о токенах в переменные
bot_token = os.environ['bot']
TGbot = telebot.TeleBot(bot_token)

# запросы к API Binance
client = Client(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
try:
    get_all_price = client.get_all_tickers()
except BinanceRequestException:
    print('формат вывода отличен от JSON')
except BinanceAPIException as bapi:
    print('Ошибка вызова API, код ошибки Binance - ' + bapi.code)

# функция получения курса доллара и евро


def get_price_eurusd():
    # ссылка на страницу с курсами
    curr_url = 'https://finance.rambler.ru/currencies/'
    # XPATH ссылки на нужные значения
    usd_value_xpath = '/html/body/div[8]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[2]/label[2]/div/a[1]/div[2]'
    eur_value_xpath = '/html/body/div[8]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[2]/label[2]/div/a[2]/div[2]'
    # делаем запрос и получаем ответ\
    req = 0
    try:
        req = requests.get(curr_url)
    except req == 'Response [400]':
        print('Плохой запрос')
    except req == 'Response [403]':
        print('Запрещено')
    except req == 'Response [404]':
        print('Не найден')
    except req == 'Response [408]':
        print('Неиспользуемое соединение')
    except req == 'Response [409]':
        print('Конфликт')
    except req == 'Response [417]':
        print('Ожидание не может быть выполнено')
    except req == 'Response [500]':
        print('Внутренняя ошибка сервера')
    except req == 'Response [502]':
        print('Плохой шлюз')
    except req == 'Response [503]':
        print('Сервис недоступен')
    except req == 'Response [504]':
        print('Шлюз не доступен')
    else:
        print('Ошибка')
    # заворачиваем ответ `req.text` в StringIO и передаем парсеру, указываем чем хотим спарсить
    html_tree = etree.parse(StringIO(req.text), etree.HTMLParser())
    # возвращается список всех совпадений с XPATH на странице, берем первый и единственный для каждой валюты
    usd_val_raw = html_tree.xpath(usd_value_xpath)[0]
    eur_val_raw = html_tree.xpath(eur_value_xpath)[0]
    # получаем текст и удаляем лишнее
    usd_val = usd_val_raw.text.strip()
    eur_val = eur_val_raw.text.strip()
    return usd_val, eur_val


# функция получения курса биткоина и эфира
def get_price_btceth():
    btc_price = 0
    eth_price = 0
    for i in get_all_price:
        if i['symbol'] == 'BTCUSDT':
            btc_price = i['price']
        if i['symbol'] == 'ETHUSDT':
            eth_price = i['price']
    return btc_price, eth_price

# функция запуска бота и вывода данных о курсе


def start():
    while True:
        # переменные для получения даных из функций
        btceth = get_price_btceth()
        eurusd = get_price_eurusd()
        # переменные для вывода
        btc = float(btceth[0])
        eth = float(btceth[1])
        usd = float(eurusd[0])
        eur = float(eurusd[1])
        # вывод данных в бота
        try:
            TGbot.send_message("@currencyofmoney", f'Курс BTC {btc:.2f} $\nКурс ETH {eth:.2f} $\n'
                                                   f'Курс USD {usd:.2f} ₽\nКурс EUR {eur:.2f} ₽')
            time.sleep(1800)
        except telebot.apihelper.ApiException:
            print('Не удалось отправить сообщение')
        # проверка вызова функции


if __name__ == '__main__':
    start()
