
import telebot
from telebot import types

TOKEN = "7181297811:AAH-9mrQxoo6fJbJ0XdTx8bHskvMvzzC6wI"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🟢 Submit Gmail", "💳 Balance")
    markup.row("📤 Payout Request", "📨 My Submissions")
    bot.send_message(
        message.chat.id,
        f"Welcome {message.from_user.first_name} to Gmail Buy Sell BD!",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "🟢 Submit Gmail":
        bot.send_message(message.chat.id, "Please send your Gmail address:")
    elif message.text == "💳 Balance":
        bot.send_message(message.chat.id, "Your balance: 0৳")
    elif message.text == "📤 Payout Request":
        bot.send_message(message.chat.id, "Minimum 25৳ required. Send number and method (bKash/Nagad).")
    elif message.text == "📨 My Submissions":
        bot.send_message(message.chat.id, "You have no submissions yet.")
    else:
        bot.send_message(message.chat.id, "Invalid command.")

import flask
from flask import Flask, request

app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'ok', 200

@app.route('/')
def index():
    return 'Bot is running!', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
