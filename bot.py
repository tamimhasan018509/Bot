import telebot
from telebot import types
import json
import os

# Bot Token
TOKEN = '8078197774:AAFnlPOffx9lwR3iYeeMCB1AvATxQUO51s8'

# Admin Telegram ID
ADMIN_ID = 6803843822

# Channel to join
CHANNEL_USERNAME = "@developer_abir_bd"

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# User database (simple JSON file)
DB_FILE = "users.json"

# Load user data
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(DB_FILE, "w") as f:
        json.dump(users, f)

# Check if user joined channel
def is_user_joined(chat_member):
    return chat_member.status in ["member", "administrator", "creator"]

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    referral = args[1] if len(args) > 1 else None

    # Check if already registered
    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "referrals": [],
            "withdraw_request": None
        }
        if referral and referral != user_id and referral in users:
            users[referral]["balance"] += 75
            users[referral]["referrals"].append(user_id)
            save_users()

    # Channel join check
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, message.chat.id)
        if not is_user_joined(chat_member):
            markup = types.InlineKeyboardMarkup()
            join_button = types.InlineKeyboardButton("✅ চ্যানেল জয়েন করুন", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
            markup.add(join_button)
            bot.send_message(message.chat.id, "প্রথমে আমাদের চ্যানেলে জয়েন করুন!", reply_markup=markup)
            return
    except Exception as e:
        print(e)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🏦 ব্যালেন্স", "👥 রেফারেল লিঙ্ক", "💸 উইথড্র")
    bot.send_message(message.chat.id, "স্বাগতম! মেনু থেকে একটি অপশন বেছে নিন:", reply_markup=markup)
    save_users()

# Balance
@bot.message_handler(func=lambda message: message.text == "🏦 ব্যালেন্স")
def balance(message):
    user_id = str(message.from_user.id)
    balance = users.get(user_id, {}).get("balance", 0)
    bot.send_message(message.chat.id, f"আপনার ব্যালেন্স: {balance} পয়েন্ট")

# Referral Link
@bot.message_handler(func=lambda message: message.text == "👥 রেফারেল লিঙ্ক")
def referral_link(message):
    user_id = str(message.from_user.id)
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(message.chat.id, f"আপনার রেফারেল লিঙ্ক:\n{link}")

# Withdraw
@bot.message_handler(func=lambda message: message.text == "💸 উইথড্র")
def withdraw(message):
    user_id = str(message.from_user.id)
    balance = users.get(user_id, {}).get("balance", 0)

    if balance < 500:
        bot.send_message(message.chat.id, "উইথড্র করার জন্য কমপক্ষে ৫০০ পয়েন্ট লাগবে।")
        return

    msg = bot.send_message(message.chat.id, "আপনার Dogs Address পাঠান:")
    bot.register_next_step_handler(msg, process_withdraw)

def process_withdraw(message):
    user_id = str(message.from_user.id)
    address = message.text

    users[user_id]["withdraw_request"] = address
    save_users()

    # Notify admin
    bot.send_message(ADMIN_ID, f"নতুন উইথড্র রিকোয়েস্ট:\n\nUser ID: {user_id}\nDogs Address: {address}\nBalance: {users[user_id]['balance']}")

    bot.send_message(message.chat.id, "আপনার উইথড্র রিকোয়েস্ট গ্রহণ করা হয়েছে। এডমিন শীঘ্রই রিভিউ করবেন।")

# Admin Commands
@bot.message_handler(commands=['panel'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("👤 ইউজার চেক", "📥 উইথড্র রিকোয়েস্ট")
        bot.send_message(message.chat.id, "এডমিন প্যানেল:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "👤 ইউজার চেক")
def check_users(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"মোট ইউজার: {len(users)} জন")

@bot.message_handler(func=lambda message: message.text == "📥 উইথড্র রিকোয়েস্ট")
def withdraw_requests(message):
    if message.from_user.id == ADMIN_ID:
        requests = [f"User: {uid}\nAddress: {info['withdraw_request']}" for uid, info in users.items() if info.get("withdraw_request")]
        if requests:
            bot.send_message(message.chat.id, "\n\n".join(requests))
        else:
            bot.send_message(message.chat.id, "কোনো উইথড্র রিকোয়েস্ট নেই।")

# Run the bot
bot.infinity_polling()