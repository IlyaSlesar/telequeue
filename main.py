import telebot
from db import User, Booking

with open('api_keys', 'r') as f:
    api_keys = f.readline()

bot = telebot.TeleBot(api_keys, parse_mode=None)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 'Напиши /register [ФИО], чтобы зарегистрироваться ' + message.text)

@bot.message_handler(commands=['register'])
def register_user(message):
    user = User.create(id=message.from_user.id, name=' '.join(message.text.split(' ')[1:]))
    user.save()

bot.infinity_polling()