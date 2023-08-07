# требуемые библиотеки
import requests
import telebot
import time
import os
from binance.exceptions import BinanceRequestException
from binance.exceptions import BinanceAPIException
from binance.client import Client
from dotenv import load_dotenv
from io import StringIO  # требование для парсера LXML, он работает со строками асинхронно как с файлами
from lxml import etree  # базовый модуль парсера
from requests.exceptions import RequestException


# добавляем токены бинанса для доступа к API
dotenv_path = os.path.join(os.path.dirname(__file__), 'tokens.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print('Путь к файлу или файл не существует')
    exit(-1)


# передаём данные о токенах в переменные
bot_token = os.environ['bot']
TGbot = telebot.TeleBot(bot_token)

# запросы к API Binance
client = Client(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])


# функция получения курса доллара и евро


def get_price_eurusd():
    # ссылка на страницу с курсами
    curr_url = 'https://finance.rambler.ru/currencies/'
    # XPATH ссылки на нужные значения
    usd_value_xpath = '/html/body/div[8]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[2]/label[2]/div/a[1]/div[2]'
    eur_value_xpath = '/html/body/div[8]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[2]/label[2]/div/a[2]/div[2]'
    # делаем запрос и получаем ответ
    req = requests.get(curr_url)
    if req.status_code != requests.codes.ok:
        raise ValueError('Статус код не равен 200')
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
    get_all_price = client.get_all_tickers()
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
        try:
            btceth = get_price_btceth()
        except BinanceRequestException:
            print('Проблема на стороне Бинанса при запросе данных')
            time.sleep(60)
            continue
        # прописать действия в случае ошибки(что будет дальше делать программа)
        except BinanceAPIException as bapi:
            print('Ошибка вызова API, код ошибки Binance: ', bapi.code, bapi.message)
            break
        # переменные для получения даных из функций
        try:
            eurusd = get_price_eurusd()
        except RequestException as e:
            print('Ошибка запроса к Рамблеру', type(e), e)
            time.sleep(60)
            continue
        except ValueError as v:
            print(type(v), v)
            time.sleep(60)
            continue
        # переменные для вывода
        btc = float(btceth[0])
        eth = float(btceth[1])
        usd = float(eurusd[0])
        eur = float(eurusd[1])
        # отправка сообщения в канал
        try:
            TGbot.send_message("@currencyofmoney", f'Курс BTC {btc:.2f} $\nКурс ETH {eth:.2f} $\n'
                                                   f'Курс USD {usd:.2f} ₽\nКурс EUR {eur:.2f} ₽')
            time.sleep(1800)
        except telebot.apihelper.ApiException as e:
            print('Не удалось отправить сообщение: ', type(e), e)
            time.sleep(10)
            continue
        # проверка вызова функции


if __name__ == '__main__':
    try:
        start()
    except Exception as m:
        print('Непредвиденная ошибка:', type(m), m)
        exit(-1)
