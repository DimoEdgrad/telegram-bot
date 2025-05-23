
import json
import time
from telebot import TeleBot
from flask import Flask
from threading import Thread

# Load config
with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

bot = TeleBot(config["bot_token"])

# Load or initialize users
try:
    with open("users.json", "r", encoding="utf-8") as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

def save_users():
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def load_lang(key, lang):
    try:
        with open(f"lang/{lang}.json", encoding="utf-8") as f:
            strings = json.load(f)
        return strings.get(key, key)
    except:
        return key

def get_user_lang(user_id):
    return users.get(str(user_id), {}).get("lang", config["default_lang"])

@bot.message_handler(commands=['start'])
def start(message):
    lang = get_user_lang(message.from_user.id)
    bot.reply_to(message, load_lang("start", lang))

@bot.message_handler(commands=['help'])
def help_cmd(message):
    lang = get_user_lang(message.from_user.id)
    bot.reply_to(message, load_lang("help", lang))

@bot.message_handler(func=lambda msg: msg.text.startswith("/add"))
def add_user(message):
    if message.from_user.id not in config["admin_ids"]:
        return
    parts = message.text.split()
    if len(parts) < 2:
        return
    uid = parts[1]
    days = int(parts[2]) if len(parts) > 2 else 30
    users[uid] = users.get(uid, {})
    users[uid]["expire"] = int(time.time()) + days * 86400
    users[uid]["lang"] = users[uid].get("lang", config["default_lang"])
    save_users()
    bot.reply_to(message, load_lang("added", get_user_lang(message.from_user.id)))

@bot.message_handler(func=lambda msg: msg.text.startswith("/extend"))
def extend_user(message):
    if message.from_user.id not in config["admin_ids"]:
        return
    parts = message.text.split()
    if len(parts) < 3:
        return
    uid = parts[1]
    days = int(parts[2])
    if uid in users:
        users[uid]["expire"] += days * 86400
        save_users()
        bot.reply_to(message, load_lang("extended", get_user_lang(message.from_user.id)))

@bot.message_handler(func=lambda msg: msg.text.startswith("/del"))
def del_user(message):
    if message.from_user.id not in config["admin_ids"]:
        return
    parts = message.text.split()
    if len(parts) < 2:
        return
    uid = parts[1]
    if uid in users:
        del users[uid]
        save_users()
        bot.reply_to(message, load_lang("deleted", get_user_lang(message.from_user.id)))

@bot.message_handler(commands=['list'])
def list_users(message):
    if message.from_user.id not in config["admin_ids"]:
        return
    msg = "\n".join([f"{uid}: expires at {time.ctime(u['expire'])}" for uid, u in users.items()])
    bot.reply_to(message, msg or "No users found")

# Flask server to keep alive (for Replit/UptimeRobot)
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def keep_alive():
    Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8080}).start()

keep_alive()
bot.polling(non_stop=True)
