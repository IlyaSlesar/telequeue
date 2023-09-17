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
with open('locale.yml') as f:
    locale = yaml.safe_load(f.read())

db.create_tables([User, Booking])
bot = telebot.TeleBot(config['api_key'], parse_mode=None)

def check_rights(message):
    have_rights = message.from_user.id in config['admins']
    if not have_rights:
        bot.reply_to(message, locale['no_rights'])
    return have_rights

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, locale['help'])
    if message.from_user.id in config['admins']:
        bot.reply_to(message, locale['help_adm'])

@bot.message_handler(commands=['register'])
def register(message):
    user_check_tid = User.select().where(User.t_id == str(message.from_user.id))
    if len(user_check_tid) != 0:
        bot.reply_to(message, locale['already_registered'])
        return
    bot.reply_to(message, locale['input_username'])
    bot.register_next_step_handler(message, register_process_username)

def check_username(message):
    if len(message.text) < 3:
        bot.reply_to(message, locale['short_username'])
        return False
    for sym in message.text:
        if sym != ' ':
            break
    else:
        bot.reply_to(message, locale['empty_username'])
        return False
    user_check_name = User.select().where(User.name == message.text)
    if len(user_check_name) != 0:
        bot.reply_to(message, locale['taken_username'])
        return False
    return True

def register_process_username(message):
    if not check_username(message):
        return
    user = User.create(t_id=message.from_user.id, name=message.text)
    user.save()
    bot.reply_to(message, locale['registration_success'])

@bot.message_handler(commands=['join', 'enqueue'])
def enqueue(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    if len(user) != 1:
        bot.reply_to(message, locale['registration_required'])
        return
    if config['modules']:
        bot.reply_to(message, locale['input_module'])
        bot.register_next_step_handler(message, enqueue_process_module)
        return
    booking = Booking.create(owner=user, module=0)
    booking.save()
    bot.reply_to(message, locale['enqueue_success'])
    bot.reply_to(message, locale['exit_reminder'])
    queue_change_notify()
    
def enqueue_process_module(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    module = int(message.text)
    if not (module <= 5 and module >= 1):
        bot.reply_to(message, locale['incorrect_module'])
        return
    number_of_places = Booking.select().where(Booking.owner == user, Booking.module == module)
    if len(number_of_places) > 0:
        bot.reply_to(message, locale['already_enqueued'])
        return
    booking = Booking.create(owner=user, module=module)
    booking.save()
    bot.reply_to(message, locale['enqueue_success'])
    bot.reply_to(message, locale['exit_reminder'])
    queue_change_notify()


@bot.message_handler(commands=['exit', 'leave'])
def dequeue(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    if len(user) != 1:
        bot.reply_to(message, locale['registration_required'])
        return
    if config['modules']:
        bot.reply_to(locale['input_module'])
        bot.register_next_step_handler(message, dequeue_process_module)
        return
    booking = Booking.select().where(Booking.owner == user)
    if len(booking) == 0:
        bot.reply_to(message, locale['not_enqueued'])
        return
    booking[0].delete_instance()
    bot.reply_to(message, locale['dequeue_success'])
    queue_change_notify()

def dequeue_process_module(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    booking = Booking.select().where(Booking.owner == user, booking.module == int(message.text))
    if len(booking) == 0:
        bot.reply_to(message, locale['not_enqueued'])
        return
    booking[0].delete_instance()
    bot.reply_to(message, locale['dequeue_success'])
    queue_change_notify()

@bot.message_handler(commands=['rename'])
def rename(message):
    user = User.select().where(User.t_id == str(message.from_user.id))
    if len(user) != 1:
        bot.reply_to(message, locale['registration_required'])
        return
    bot.reply_to(message, locale['input_username'])
    bot.register_next_step_handler(message, partial(rename_proccess_name, user=user[0]))

def rename_proccess_name(message, user):
    if not check_username(message):
        return
    user.name = message.text
    user.save()
    bot.reply_to(message, locale['rename_success'])

@bot.message_handler(commands=['list_users'])
def list_users(message):
    if not check_rights(message):
        return
    user_list = ''
    for i, user in enumerate(User.select()):
        user_list += f'{i + 1}. {user.name} {user.t_id}\n'
    if not user_list:
        user_list = locale['no_users']
    bot.reply_to(message, user_list)

@bot.message_handler(commands=['kick'])
def kick(message):
    if not check_rights(message):
        return
    queue = list_queue(True)
    if queue == 'Очередь пуста\n':
        bot.reply_to(message, queue)
        return
    bot.reply_to(message, queue)
    bot.reply_to(message, locale['input_user_id'])
    bot.register_next_step_handler(message, kick_proccess_tid)

def kick_proccess_tid(message):
    user = User.select().where(User.t_id == message.text)
    if len(user) == 0:
        bot.reply_to(message, locale['no_such_user'])
        return
    if config['modules']:
        bot.reply_to(message, locale['input_module'])
        bot.register_next_step_handler(message, partial(kick_process_module, user=user))
        return
    
    booking = Booking.select().where(Booking.owner == user)
    if len(booking) == 0:
        bot.reply_to(message, locale['user_not_enqueued'])
        return
    booking[0].delete_instance()
    bot.reply_to(message, locale['kick_success'])
    queue_change_notify()

def kick_process_module(message, user):
    booking = Booking.select().where(Booking.owner == user, Booking.module == int(message.text))
    if len(booking) == 0:
        bot.reply_to(message, locale['user_not_enqueued'])
        return
    booking[0].delete_instance()
    bot.reply_to(message, locale['kick_success'])
    queue_change_notify()

@bot.message_handler(commands=['kick_first'])
def kick_first(message):
    if not check_rights(message):
        return
    booking = Booking.select()
    if len(booking) == 0:
        bot.reply_to(message, locale['empy_queue'])
        return
    booking[0].delete_instance()
    bot.reply_to(message, locale['kick_success'])
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
                queue += f'{pos}. {booking.owner.name} ({locale.module} {booking.module}) {booking.owner.t_id if include_ids else str()}\n'
                pos += 1
    else:
        for pos, booking in enumerate(Booking.select()):
            queue += f'{pos + 1}. {booking.owner.name} {booking.owner.t_id if include_ids else str()}\n'
    if not queue:
        queue = locale["empty_queue"] + '\n'
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
        bot.send_message(user.t_id, locale['updated_queue'])
        bot.send_message(user.t_id, list_queue())
        if user.t_id == first[0]:
            if config['modules']:
                bot.send_message(user.t_id, locale['congrats_module'].format(first[1]))
            else:
                bot.send_message(user.t_id, locale['congrats'])
            bot.send_sticker(user.t_id, locale['congrats_sticker'])
        
bot.infinity_polling()
db.close()