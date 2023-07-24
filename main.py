# требуемые библиотеки
import requests
import telebot
import time
import os
from binance.client import Client
from dotenv import load_dotenv
from io import StringIO # требование для парсера LXML, он работает со строками асинхронно как с файлами
from lxml import etree # базовый модуль парсера

# добавляем токены бинанса для доступа к API
dotenv_path = os.path.join(os.path.dirname(__file__), 'tokens.env')
if os.path.exists(dotenv_path):
   load_dotenv(dotenv_path)

# передаём данные о токенах в переменные
bot_token = os.environ['bot']
TGbot = telebot.TeleBot(bot_token)

# запросы к API Binance
client = Client(api_key=os.environ['API_KEY'], api_secret=os.environ['API_SECRET'])
get_all_price = client.get_all_tickers()

# функция получения курса доллара и евро
def get_price_EURUSD():
# ссылка на страницу с курсами
    CURR_URL = 'https://finance.rambler.ru/currencies/'
# XPATH ссылки на нужные значения
    USD_VALUE_XPATH = '/html/body/div[8]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[2]/label[2]/div/a[1]/div[2]'
    EUR_VALUE_XPATH = '/html/body/div[8]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[2]/label[2]/div/a[2]/div[2]'
# делаем запрос и получаем ответ
    req = requests.get(CURR_URL)
# заворачиваем ответ `req.text` в StringIO и передаем парсеру, указываем чем хотим спарсить
    html_tree = etree.parse(StringIO(req.text), etree.HTMLParser())
# получаем значения. возвращается список всех совпадений с XPATH на странице, берем первый и единственный для каждой валюты
    usd_val_raw = html_tree.xpath(USD_VALUE_XPATH)[0]
    eur_val_raw = html_tree.xpath(EUR_VALUE_XPATH)[0]
# получаем текст и удаляем лишнее
    usd_val = usd_val_raw.text.strip()
    eur_val = eur_val_raw.text.strip()
    return usd_val, eur_val

# функция получения курса биткоина и эфира
def get_price_BTCETH():
    get_all_price = client.get_all_tickers()
    for i in get_all_price:
        if i['symbol'] == 'BTCUSDT':
            BTC_price = i['price']
        if i['symbol'] == 'ETHUSDT':
            ETH_price = i['price']
    return BTC_price, ETH_price

# функция запуска бота и вывода данных о курсе
def start():
    while True:
# переменные для получения даных из функций
        BTCETH = get_price_BTCETH()
        EURUSD = get_price_EURUSD()
# переменные для вывода
        BTC = float(BTCETH[0])
        ETH = float(BTCETH[1])
        USD = float(EURUSD[0])
        EUR = float(EURUSD[1])
# вывод данных в бота
        TGbot.send_message("@currencyofmoney", f'Курс BTC {BTC:.2f} $\nКурс ETH {ETH:.2f} $\n'f'Курс USD {USD:.2f} ₽\nКурс EUR {EUR:.2f} ₽')
        time.sleep(1800)
# проверка вызова функции
if __name__ == '__main__':
    start()
