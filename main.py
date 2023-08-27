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
import seaborn as sns
from PIL import Image
import matplotlib.pyplot as plt
import io
from datetime import datetime


# функция записи времени в секундах для построения графиков
def register_data(btc, eth, usd, eur):
    x = int(time.time())
    with open(f'data/data_btc.csv', 'a+') as f:
        f.write(f'{x},{btc},BTC\n')
    with open(f'data/data_eth.csv', 'a+') as f:
        f.write(f'{x},{eth},ETH\n')
    with open(f'data/data_usd.csv', 'a+') as f:
        f.write(f'{x},{usd},USD\n')
    with open(f'data/data_eur.csv', 'a+') as f:
        f.write(f'{x},{eur},EUR\n')


# функция получения данных для построения графиков
def load_data(curr):
    data_buf = {'Date': [], 'Val': [], 'Cur': []}
    with open(f'data/data_{curr}.csv', 'r') as fp:
        for raw_line in fp:
            line = raw_line.strip()

            if not (len(line) > 0):
                continue
            data = line.split(',')
            date = int(data[0])
            price = float(data[1])
            cur = data[2]
            if int(time.time()) - date > (60 * 60 * 24 * 5):
                continue
            data_buf['Date'].append(date)
            data_buf['Val'].append(price)
            data_buf['Cur'].append(cur)

    return data_buf


# Устанавливаем цвета графиков
palette_btc = [(0.9616917, 0.8007763, 0.5606593)]
palette_eth = [(0.50381595, 0.10373781, 0.99769923)]
palette_usd = [(0.5616917, 0.70776351, 0.5606593)]
palette_eur = [(0.10381595, 0.70373781, 0.99769923)]


# функция создания графиков четырех валют
def create_plots(data, palette):

    # Строим график btc
    sns.set_theme(style="ticks")

    fig, ax = plt.subplots()
    sns_plot = sns.lineplot(

        data=data,
        x='Date',
        y='Val',
        hue='Cur',
        palette=palette,
        ax=ax
    )

    plt.legend(loc='best')
    sns_plot.set(xlabel=None)
    sns_plot.set(ylabel=None)

    time_data = data['Date']
    time_new = []
    for x in range(len(time_data)):
        if x % 32 == 0:
            time_new.append(time_data[x])

    # Замена секунд на дату по оси x
    plt.xticks(time_new, [datetime.utcfromtimestamp(x).strftime('%m-%d') for x in time_new])
    buffer = io.BytesIO()

    sns_plot.figure.savefig(buffer)

    plt.close()
    return buffer


# функция построения и объединения графиков четырех валют в один рисунок
def merge_plots():
    data_btc = load_data('btc')
    data_eth = load_data('eth')
    data_usd = load_data('usd')
    data_eur = load_data('eur')

    buffer_btc = create_plots(data_btc, palette_btc)
    buffer_eth = create_plots(data_eth, palette_eth)
    buffer_usd = create_plots(data_usd, palette_usd)
    buffer_eur = create_plots(data_eur, palette_eur)

    # Открываем созданные графики
    img_btc = Image.open(buffer_btc)
    img_eth = Image.open(buffer_eth)
    img_usd = Image.open(buffer_usd)
    img_eur = Image.open(buffer_eur)

    img_size = img_btc.size

    new_im = Image.new('RGB', (2*img_size[0] - 50, 2*img_size[1] - 25), (250, 250, 250))

    new_im.paste(img_btc, (0, 0))
    new_im.paste(img_eur, (img_size[0] - 50, 0))
    new_im.paste(img_eth, (0, img_size[1] - 25))
    new_im.paste(img_usd, (img_size[0] - 50, img_size[1] - 25))
    new_im.save("merged_images.png", "PNG")


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
        # Получаем курс криптовалют с Бинанса
        try:
            btceth = get_price_btceth()
        except BinanceRequestException:
            print('Проблема на стороне Бинанса при запросе данных')
            time.sleep(60)
            continue
        except BinanceAPIException as bapi:
            print('Ошибка вызова API, код ошибки Binance: ', bapi.code, bapi.message)
            break
        # Получаем курсы валют с Рамблера
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

        # запись данных в списки для построения графиков
        try:
            register_data(btc, eth, usd, eur)
        except OSError as v:
            print(type(v), v)
            time.sleep(60)
            continue

        # вызов функции построения и объединения графиков
        merge_plots()
        # отправка сообщения в канал
        try:
            TGbot.send_photo("@currencyofmoney",
                             photo=open('merged_images.png', 'rb'),
                             caption=f'Курс BTC {btc:.2f}$\nКурс ETH {eth:.2f}$\n'
                             f'Курс EUR {eur:.2f}₽\nКурс USD {usd:.2f}₽ ')
            os.remove("merged_images.png")
            time.sleep(1800)
        except telebot.apihelper.ApiException as e:
            print('Не удалось отправить сообщение или графики: ', type(e), e)
            time.sleep(10)
            continue


# проверка вызова функции
if __name__ == '__main__':
    try:
        start()
    except Exception as m:
        print('Непредвиденная ошибка:', type(m), m)
        exit(-1)
