from functools import partial
import telebot
import yaml
from db import User, Booking, db

with open('config.yml', 'r') as f:
    config_raw = f.read()
    config = yaml.safe_load(config_raw)
if 'api_key' not in config:
    print('No api_key in config. Exiting.')
    exit()

db.create_tables([User, Booking])
bot = telebot.TeleBot(config['api_key'], parse_mode=None)

def check_rights(message):
    have_rights = message.from_user.id in config['admins']
    if not have_rights:
        bot.reply_to(message, 'У вас нет прав выполнить эту команду')
    return have_rights

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 'Напиши /register, чтобы зарегистрироваться')

@bot.message_handler(commands=['register'])
def register(message):
    user_check_tid = User.select().where(User.t_id == str(message.from_user.id))
    if len(user_check_tid) != 0:
        bot.reply_to(message, 'Вы уже зарегистрированны')
        return
    bot.reply_to(message, 'Введите своё ФИО')
    bot.register_next_step_handler(message, register_process_username)

def register_process_username(message):
    if len(message.text) < 3:
        bot.reply_to(message, 'Имя должно содержать более 3 символов')
        return
    for sym in message.text:
        if sym != ' ':
            break
    else:
        bot.reply_to(message, 'Имя не должно быть пустым')
        return
    user_check_name = User.select().where(User.name == message.text)
    if len(user_check_name) != 0:
        bot.reply_to(message, 'Данное имя уже занято')
        return
    user = User.create(t_id=message.from_user.id, name=message.text)
    user.save()
    bot.reply_to(message, 'Вы успешно зарегистрированы!\nЧтобы встать в очередь, напишите /join \
                 \nЧтобы посмотреть очередь, напишите /queue')

@bot.message_handler(commands=['join', 'enqueue'])
def enqueue(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    if len(user) != 1:
        bot.reply_to(message, 'Прежде чем добавиться в очередь необходимо зарегистрироваться с помощью команды /register')
        return
    if config['modules']:
        bot.reply_to(message, 'Введите номер модуля, который будете сдавать')
        bot.register_next_step_handler(message, enqueue_process_module)
        return
    booking = Booking.create(owner=user, module=0)
    booking.save()
    bot.reply_to(message, 'Вы встали в очередь. Когда она подойдет - придёт уведомление.')
    bot.reply_to(message, 'Как только вы ответите - сразу напишите /exit. \
                \nТак следующий человек поймет, что ему пора отвечать.')
    queue_change_notify()
    
def enqueue_process_module(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    module = int(message.text)
    if not (module <= 5 and module >= 1):
        bot.reply_to(message, 'Модуль должен быть цифрой от 1 до 5')
        return
    number_of_places = Booking.select().where(Booking.owner == user, Booking.module == module)
    if len(number_of_places) > 0:
        bot.reply_to(message, 'Вы уже находитесь в очереди на сдачу этого модуля.')
        return
    booking = Booking.create(owner=user, module=module)
    booking.save()
    bot.reply_to(message, 'Вы встали в очередь. Когда она подойдет - придет уведомление.')
    bot.reply_to(message, 'Как только вы ответите - сразу напишите /exit. \
                 \nТак следующий человек поймет, что ему пора отвечать.')
    queue_change_notify()


@bot.message_handler(commands=['exit', 'leave'])
def dequeue(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    if len(user) != 1:
        bot.reply_to(message, 'Зарегистрируйтесь с помощью команды /register [ФИО].')
        return
    if config['modules']:
        bot.reply_to('Введите номер модуля, который передумали сдавать')
        bot.register_next_step_handler(message, dequeue_process_module)
        return
    booking = Booking.select().where(Booking.owner == user)
    if len(booking) == 0:
        bot.reply_to(message, 'Вы не находитесь в очереди.')
        return
    booking[0].delete_instance()
    bot.reply_to(message, 'Вы успешно вышли из очереди.')
    queue_change_notify()

def dequeue_process_module(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    booking = Booking.select().where(Booking.owner == user, booking.module == int(message.text))
    if len(booking) == 0:
        bot.reply_to(message, 'Вы не находитесь в очереди.')
        return
    booking[0].delete_instance()
    bot.reply_to(message, 'Вы успешно вышли из очереди.')
    queue_change_notify()

@bot.message_handler(commands=['list_users'])
def list_users(message):
    if not check_rights(message):
        return
    user_list = ''
    for i, user in enumerate(User.select()):
        user_list += f'{i + 1}. {user.name} {user.t_id}\n'
    if not user_list:
        user_list = 'Нет зарегистрированных пользователей.'
    bot.reply_to(message, user_list)

@bot.message_handler(commands=['kick'])
def kick(message):
    if not check_rights(message):
        return
    queue = list_queue(True)
    if queue == 'Очередь пуста\n':
        bot.reply_to(message, queue)
        return
    bot.reply_to(message, 'Выберите пользователя:\n' + queue + 'Введите его id')
    bot.register_next_step_handler(message, kick_proccess_tid)

def kick_proccess_tid(message):
    user = User.select().where(User.t_id == message.text)
    if len(user) == 0:
        bot.reply_to(message, 'Нет такого пользователя')
        return
    if config['modules']:
        bot.reply_to(message, 'Введите модуль')
        bot.register_next_step_handler(message, partial(kick_process_module, user=user))
        return
    
    booking = Booking.select().where(Booking.owner == user)
    if len(booking) == 0:
        bot.reply_to(message, 'Этот пользователь не занимал место в очереди')
        return
    booking[0].delete_instance()
    bot.reply_to(message, 'Пользователь успешно удалён из очереди')
    queue_change_notify()

def kick_process_module(message, user):
    booking = Booking.select().where(Booking.owner == user, Booking.module == int(message.text))
    if len(booking) == 0:
        bot.reply_to(message, 'Этот пользователь не занимал место в очереди на сдачу этого модуля')
        return
    booking[0].delete_instance()
    bot.reply_to(message, 'Пользователь успешно удалён из очереди')
    queue_change_notify()

@bot.message_handler(commands=['kick_first'])
def kick_first(message):
    if not check_rights(message):
        return
    booking = Booking.select()
    if len(booking) == 0:
        bot.reply_to(message, 'Очередь пуста')
        return
    booking[0].delete_instance()
    bot.reply_to(message, 'Самый первый элемент очереди успешно удалён')
    queue_change_notify()

@bot.message_handler(commands=['queue', 'list_queue', 'bookings'])
def send_queue(message):
    bot.reply_to(message, list_queue())

def list_queue(include_ids = False):
    queue = ''
    if config['modules']:
        pos = 1
        for module in range(1, 5):
            for booking in Booking.select().where(Booking.module == module):
                queue += f'{pos}. {booking.owner.name} (Модуль {booking.module}) {booking.owner.t_id if include_ids else str()}\n'
                pos += 1
    else:
        for pos, booking in enumerate(Booking.select()):
            queue += f'{pos + 1}. {booking.owner.name} {booking.owner.t_id if include_ids else str()}\n'
    if not queue:
        queue = 'Очередь пуста\n'
    return queue

def queue_change_notify():
    
    if config['modules']:
        first = (0,0)
        for module in range(1, 5):
            booking = Booking.select().where(Booking.module == module)
            if len(booking) > 0:
                first = (booking[0].owner.t_id, booking[0].module)
                break
    else:
        first = (0,)
        bookings = Booking.select()
        if len(bookings) > 0:
            first = (bookings[0].owner.t_id,)
    
    for user in User.select():
        bot.send_message(user.t_id, 'Очередь обновилась:')
        bot.send_message(user.t_id, list_queue())
        if user.t_id == first[0]:
            if config['modules']:
                bot.send_message(user.t_id, f'Поздравляем! Подошла твоя очередь на сдачу {first[1]} модуля! Не забудь написать /exit как сдашь работу!')
            else:
                bot.send_message(user.t_id, f'Поздравляем! Подошла твоя очередь! Не забудь написать /exit как сдашь работу!')
            bot.send_sticker(user.t_id, "CAACAgIAAxkBAAEKTGVlA04aQN6QF-xrZqcTr2EhmrqFmQACGwADwDZPE329ioPLRE1qMAQ")
        
bot.infinity_polling()
db.close()