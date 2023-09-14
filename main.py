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
        bot.reply_to(message, 'У вас нет прав выполнить эту команду.')
    return have_rights


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 'Напиши /register [ФИО], чтобы зарегистрироваться.')

@bot.message_handler(commands=['register'])
def register_user(message):
    existing_user = User.select().where(User.t_id == str(message.from_user.id))
    if len(existing_user) != 0:
        bot.reply_to(message, 'С данного телеграм аккаунта уже создан пользователь.')
        return
    user = User.create(t_id=message.from_user.id, name=' '.join(message.text.split(' ')[1:]))
    user.save()
    bot.reply_to(message, 'Вы успешно зарегистрированы!\nЧтобы встать в очередь, напишите /join \
                 \nЧтобы посмотреть очередь, напишите /queue')

@bot.message_handler(commands=['join', 'enqueue'])
def enqueue(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    if len(user) != 1:
        bot.reply_to(message, 'Прежде чем добавиться в очередь необходимо зарегистрироваться с помощью команды /register.')
        return
    booking = Booking.create(owner=user) # position=0
    booking.save()
    bot.reply_to(message, 'Вы встали в очередь. Когда она подойдет - придет уведомление.')
    bot.reply_to(message, 'Как только вы ответите - сразу напишите /exit. \
                 \nТак следующий человек поймет, что ему пора отвечать.')

@bot.message_handler(commands=['list_users'])
def list_users(message):
    if not check_rights(message):
        return
    user_list = ''
    for i, user in enumerate(User.select()):
        user_list += f'{i}. {user.name} {user.t_id}\n'
    if not user_list:
        user_list = 'Нет зарегистрированных пользователей.'
    bot.reply_to(message, user_list)

@bot.message_handler(commands=['queue', 'list_queue', 'bookings'])
def list_queue(message):
    queue = ''
    for i, booking in enumerate(Booking.select()):
        queue += f'{i + 1}. {booking.owner.name}\n'  # {booking.position} {booking.owner.t_id}
    if not queue:
        queue = 'Очередь пуста'
    bot.reply_to(message, queue)

bot.infinity_polling()
db.close()