# TeleQueue

## English

### About
Telequeue is a Telegram bot made for maintaining an online queue. It is simple to use and setup. 

### Functionality
- basic queues
- parallell queues
- notifications for users
- admin kick from queue
- customizable messages (locale.yaml)

### Under the hood
This bot is ran in a synchronous event-loop. It interacts with Telegram API using pyTelegramBotAPI, it stores data in a single SQLite file and it uses YAML for configuration.

### How to run
0) Clone this repository
1) Install all dependencies

    `pip install -r requirements.txt`

2) Create a bot with https://t.me/BotFather and paste API key into config.yml file after `api_key: paste your api key here`
3) Run

    `python main.py`

## Русский

### О боте

Telequeue - Телеграм-бот для обеспечения электронной очереди, простой в использовании и настройке.

### Функционал
- простая очередь
- паралельные очереди
- уведомления
- администраторский кик
- настраиваемые сообщения (locale.yaml)

### Под капотом
Бот работает в синхронном event-loop. Он использует pyTelegramBotApi для работы с Телеграмом, сохраняет информацию в один SQLite файлик и использует YAML для конфигов.

### Как запустить
0) Скачать этот репозиторий
1) Установить все зависимости

    `pip install -r requirements.txt`

2) Создать Телеграм-бота с помощью https://t.me/BotFather и вставить API-ключ в config.yml: 
    
    `api_key: paste your api key here`

3) Запустить

    `python main.py`