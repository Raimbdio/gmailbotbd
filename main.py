from flask import Flask, request
import telebot

API_TOKEN = '7181297811:AAH-9mrQxoo6fJbJ0XdTx8bHskvMvzzC6wI'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Gmail Buy Sell BD!")

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "Bot is running.", 200

if __name__ == "__main__":
    app.run()
