# -*- coding: utf-8 -*-
import requests
import time
import re
import json
import sqlite3
import random
import os
import threading
from datetime import datetime
import telebot
from telebot import types

# ------------------ PANELS CONFIG (UNCHANGED) ------------------
PANELS = [
    {
        "api_url": "http://147.135.212.197/crapi/time/viewstats",
        "token": "Qk5WSjRSQmZUZZFnaWZxVYpXU4OIlFFiWU5TeohQUGhHjGZpfGhx"
    },
    {
        "api_url": "http://51.77.216.195/crapi/mait/viewstats",
        "token": "Q1NVSkNBUzRfU5GCSWqIV311gVSEa4JCX5FjeWaTbYppY26AXnFlZQ"
    },
    {
        "api_url": "http://51.77.216.195/crapi/lamix/viewstats",
        "token": "X4iWgnWXYlNhUYGJZ21PV1mEcEJpZ5RCiGSFSkN0cVw="
    },
    {
        "api_url": "http://51.77.216.195/crapi/konek/viewstats",
        "token": "X4iWgnWXYlNhUYGJZ21PV1mEcEJpZ5RCiGSFSkN0cVw="
    },
    {
        "api_url": "http://147.135.212.197/crapi/had/viewstats",
        "token": "SlNUSDRSQkWAdJKHXJWXilhOU194jphcdI6ZgYOFd2uEjWqJWIFm"
    },
    {
        "api_url": "http://pscall.net/restapi/smsreport",
        "key": "SVFWRT1SS4RygI6Ag1FQSQ==",
        "params": {
            "start": 0,
            "length": 500
        }
    }
]

# XUP SMS Credentials & Endpoints
XUP_BASE_URL = "http://108.165.233.140"
XUP_LOGIN_URL = XUP_BASE_URL + "/api/auth/login"
XUP_CODES_URL = XUP_BASE_URL + "/api/sms-codes"
XUP_USERNAME = "saboor318"
XUP_PASSWORD = "saboor318"

# ------------------ TELEGRAM & ADMIN CONFIG ------------------
TELEGRAM_BOT_TOKEN = "8128477326:AAH-NmzFoEh8hEQT8rO4kzpZRbBHYa9vdNo"
TELEGRAM_GROUP_ID = "-1003867730992"
ADMIN_IDS = [7338805216]  
DB_PATH = "panther_bot_system.db"

# Global System State Variables
BOT_ACTIVE = True  

# ------------------ MEMORY & SESSIONS ------------------
processed_ids = set()
xup_session = requests.Session()
xup_session.headers.update({"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})

# ------------------ INITIALIZE BOT Safely ------------------
try:
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, threaded=False)
    bot.delete_webhook(drop_pending_updates=True)
except Exception as e:
    print(f"❌ Initialization error: {e}")

# ------------------ ADVANCED DATABASE SETUP ------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT,
        first_name TEXT, 
        last_name TEXT,
        country_code TEXT,
        assigned_number TEXT,
        is_banned INTEGER DEFAULT 0,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS combos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code TEXT, 
        numbers TEXT,
        UNIQUE(country_code)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_sub_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_url TEXT UNIQUE NOT NULL,
        description TEXT DEFAULT '',
        enabled INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('maintenance_mode', '0')")
    conn.commit()
    conn.close()

init_db()

# ------------------ CORE SETTINGS & USER ENGINE ------------------
def is_maintenance_mode():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key='maintenance_mode'")
    row = c.fetchone()
    conn.close()
    return row[0] == '1' if row else False

def toggle_maintenance_mode(status_str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES ('maintenance_mode', ?)", (status_str,))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    existing = get_user(user_id)
    if existing:
        if country_code is None: country_code = existing[4]
        if assigned_number is None: assigned_number = existing[5]
        
    c.execute("""
        REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, last_activity)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0), CURRENT_TIMESTAMP)
    """, (user_id, username, first_name, last_name, country_code, assigned_number, user_id))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1

def update_user_activity(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET last_activity=CURRENT_TIMESTAMP WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_combo_numbers(country_code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT numbers FROM combos WHERE country_code=?", (country_code,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_combo_numbers(country_code, numbers_list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO combos (country_code, numbers) VALUES (?, ?)", (country_code, json.dumps(numbers_list)))
    conn.commit()
    conn.close()

# ------------------ SUBSCRIPTION MANAGER ------------------
def get_all_force_sub_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, channel_url, description FROM force_sub_channels WHERE enabled = 1")
    rows = c.fetchall()
    conn.close()
    return rows

def force_sub_check(user_id):
    if user_id in ADMIN_IDS:
        return True
    channels = get_all_force_sub_channels()
    if not channels:
        return True
    for _, url, _ in channels:
        try:
            if url.startswith("https://t.me/"):
                ch = "@" + url.split("/")[-1]
            elif url.startswith("@"):
                ch = url
            else:
                continue
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception:
            return False
    return True

def force_sub_markup():
    channels = get_all_force_sub_channels()
    if not channels:
        return None
    markup = types.InlineKeyboardMarkup(row_width=1)
    for _, url, desc in channels:
        text = f"📢 {desc}" if desc else "📢 Join Channel"
        markup.add(types.InlineKeyboardButton(text, url=url))
    markup.add(types.InlineKeyboardButton("✅ Verified & Joined", callback_data="verify_sub"))
    return markup

# ------------------ TELEGRAM SEND ------------------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✈️ Official Group", "url": "https://t.me/meThod5527"},
                {"text": "📱 Live Numbers", "url": "https://t.me/panthernumbers"}
            ]
        ]
    }
    
    payload = {
        "chat_id": TELEGRAM_GROUP_ID,
        "text": msg,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(keyboard)
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception:
        return False

# ------------------ GLOBAL COUNTRY DATABASE WITH FLAGS ------------------
country_codes = {
    "1": "🇺🇸 USA/Canada", 
    "7": "🇷🇺 Russia", 
    "20": "🇪🇬 Egypt", 
    "27": "🇿🇦 South Africa",
    "30": "🇬🇷 Greece", 
    "31": "🇳🇱 Netherlands", 
    "32": "🇧🇪 Belgium", 
    "33": "🇫🇷 France",
    "34": "🇪🇸 Spain", 
    "36": "🇭🇺 Hungary", 
    "39": "🇮🇹 Italy", 
    "40": "🇷🇴 Romania",
    "41": "🇨🇭 Switzerland", 
    "43": "🇦🇹 Austria", 
    "44": "🇬🇧 United Kingdom", 
    "45": "🇩🇰 Denmark",
    "46": "🇸🇪 Sweden", 
    "47": "🇳🇴 Norway", 
    "48": "🇵🇱 Poland", 
    "49": "🇩🇪 Germany",
    "60": "🇲🇾 Malaysia",
    "62": "🇮🇩 Indonesia",
    "63": "🇵🇭 Philippines",
    "65": "🇸🇬 Singapore",
    "66": "🇹🇭 Thailand",
    "81": "🇯🇵 Japan",
    "82": "🇰🇷 South Korea",
    "84": "🇻🇳 Vietnam",
    "90": "🇹🇷 Turkey",
    "91": "🇮🇳 India", 
    "92": "🇵🇰 Pakistan",
    "93": "🇦🇫 Afghanistan",
    "94": "🇱🇰 Sri Lanka",
    "95": "🇲🇲 Myanmar",
    "212": "🇲🇦 Morocco",
    "213": "🇩🇿 Algeria",
    "216": "🇹🇳 Tunisia",
    "218": "🇱🇾 Libya",
    "234": "🇳🇬 Nigeria",
    "254": "🇰🇪 Kenya",
    "351": "🇵🇹 Portugal",
    "380": "🇺🇦 Ukraine",
    "55": "🇧🇷 Brazil",
    "52": "🇲🇽 Mexico",
    "54": "🇦🇷 Argentina",
    "57": "🇨🇴 Colombia",
    "961": "🇱🇧 Lebanon",
    "962": "🇯🇴 Jordan",
    "963": "🇸🇾 Syria",
    "964": "🇮🇶 Iraq",
    "965": "🇰🇼 Kuwait",
    "966": "🇸🇦 Saudi Arabia",
    "967": "🇾🇪 Yemen",
    "968": "🇴🇲 Oman",
    "971": "🇦🇪 UAE",
    "972": "🇮🇱 Israel",
    "973": "🇧🇭 Bahrain",
    "974": "🇶🇦 Qatar",
    "994": "🇦🇿 Azerbaijan"
}

def get_country(number):
    number = str(number).replace("+", "").strip()
    for code in sorted(country_codes, key=len, reverse=True):
        if number.startswith(code):
            return country_codes[code]
    return "🌍 Global Pool"

def mask_number(number):
    number = str(number).replace("+", "").strip()
    if len(number) > 5:
        return "+" + number[:4] + "****" + number[-2:]
    return "+" + number

def extract_otp(msg):
    match = re.search(r'\b\d{3}-\d{3}\b|\b\d{4,8}\b', msg)
    return match.group(0) if match else None

def format_message(phone, otp, message, service_name="WhatsApp"):
    message = message.replace("\\n", "\n").replace("nn", "\n")
    masked = mask_number(phone)
    country = get_country(phone)
    pkt_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""
<b>New OTP Successfully Logged! 🎉</b>

<blockquote>🕰 Time: {pkt_time}</blockquote>
<blockquote>🌍 Country: {country}</blockquote>
<blockquote>📞 Target Number: {masked}</blockquote>
<blockquote>🟢 Service Platform: {service_name}</blockquote>
<blockquote>🔑 Extracted OTP: <code>{otp}</code></blockquote>

📩 Complete Payload:
<blockquote>{message}</blockquote>
"""

# ------------------ STANDARD PANEL FETCH ------------------
def fetch_sms(panel):
    try:
        params = {"key": panel["key"]} if "key" in panel else {"token": panel["token"], "records": 1000}
        if "key" in panel and "params" in panel:
            params.update(panel["params"])
        res = requests.get(panel["api_url"], params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        data = res.json()
        if isinstance(data, dict):
            return data.get("data", []) or data.get("rows", []) or data.get("codes", [])
        return data if isinstance(data, list) else []
    except Exception:
        return []

def xup_login():
    try:
        payload = {"username": XUP_USERNAME, "password": XUP_PASSWORD}
        resp = xup_session.post(XUP_LOGIN_URL, json=payload, timeout=10)
        return resp.status_code == 200
    except:
        return False

def fetch_xup_sms():
    try:
        res = xup_session.get(XUP_CODES_URL, params={"limit": 100, "page": 1}, timeout=10)
        if res.status_code in [401, 403] and xup_login():
            res = xup_session.get(XUP_CODES_URL, params={"limit": 100, "page": 1}, timeout=10)
        return res.json().get("codes", [])
    except:
        return []

# ------------------ CORE API LOOP THREAD ------------------
def main_api_processing_engine():
    xup_login()
    while True:
        if not is_maintenance_mode():
            for panel in PANELS:
                entries = fetch_sms(panel)
                for entry in entries:
                    msg = entry.get("message") or entry.get("sms") or entry.get("rawMessage") or ""
                    phone = entry.get("num") or entry.get("number") or entry.get("phone") or ""
                    date = entry.get("dt") or entry.get("dateadded") or entry.get("receivedAt") or entry.get("time") or ""
                    service_name = entry.get("sender") or entry.get("service") or "WhatsApp"
                    if not msg or not phone: continue
                    uid = f"{phone}-{msg}-{date}"
                    if uid in processed_ids: continue
                    otp = extract_otp(msg) or entry.get("code")
                    if not otp:
                        processed_ids.add(uid)
                        continue
                    final_msg = format_message(phone, otp, msg, service_name)
                    send_telegram(final_msg)
                    processed_ids.add(uid)

            xup_entries = fetch_xup_sms()
            for entry in xup_entries:
                msg = entry.get("rawMessage") or entry.get("code") or ""
                phone = entry.get("number") or ""
                date = entry.get("receivedAt") or ""
                service_name = entry.get("sender") or "WhatsApp"
                if not msg or not phone: continue
                uid = f"{phone}-{msg}-{date}"
                if uid in processed_ids: continue
                otp = extract_otp(msg) or entry.get("code")
                if not otp:
                    processed_ids.add(uid)
                    continue
                final_msg = format_message(phone, otp, msg, service_name)
                send_telegram(final_msg)
                processed_ids.add(uid)
        time.sleep(3)

# ------------------ INTERACTIVE BOT CONTROLLERS ------------------
def create_country_selection_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT country_code FROM combos")
    active_pools = [r[0] for r in c.fetchall()]
    conn.close()

    buttons = [types.InlineKeyboardButton(f"{country_codes.get(code, 'Pool')} [+{code}]", callback_data=f"pool_{code}") for code in active_pools]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start'])
def handle_start_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if is_maintenance_mode() and user_id not in ADMIN_IDS:
        bot.send_message(chat_id, "⚠️ <b>System Alert:</b>\n\nThe bot is currently under maintenance updates. Please check back later.", parse_mode="HTML")
        return

    if is_banned(user_id):
        bot.send_message(chat_id, "🚫 <b>Access Denied:</b>\n\nYou have been banned from using this automation system tool.", parse_mode="HTML")
        return

    if not force_sub_check(user_id):
        markup = force_sub_markup()
        if markup:
            bot.send_message(chat_id, "🔒 <b>Subscription Required:</b>\n\nYou must join all required verified channel layers below to unlock interaction maps.", parse_mode="HTML", reply_markup=markup)
        return

    save_user(user_id, username=message.from_user.username or "", first_name=message.from_user.first_name or "", last_name=message.from_user.last_name or "")
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("📱 Allocate Number"))
    if user_id in ADMIN_IDS:
        markup.add(types.KeyboardButton("🔐 Admin Portal"))

    bot.send_message(chat_id, f"Welcome {message.from_user.first_name} to PANTHER Engine core processing network interface.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📱 Allocate Number")
def user_allocate_number_pool(message):
    if is_banned(message.from_user.id): return
    if not force_sub_check(message.from_user.id): return
    
    markup = create_country_selection_markup()
    if not markup.keyboard:
        bot.send_message(message.chat.id, "❌ No database records initialized. Admin must update pools layer matrix.")
        return
        
    bot.send_message(message.chat.id, "🌍 <b>Select your desired Active Country Pool:</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pool_"))
def trigger_pool_distribution(call):
    user_id = call.from_user.id
    if is_banned(user_id): return
    
    code = call.data.split("_")[1]
    numbers = get_combo_numbers(code)
    if not numbers:
        bot.send_message(call.message.chat.id, "❌ Chosen network layer vector pool is empty.")
        return
        
    allocated_num = random.choice(numbers)
    save_user(user_id, country_code=code, assigned_number=allocated_num)
    
    msg_text = (
        f"🖥️ <b>SERVER STATUS:</b> ACTIVE\n"
        f"📱 <b>PLATFORM PROTOCOL:</b> WhatsApp\n"
        f"🌍 <b>COUNTRY IDENTIFIER:</b> {country_codes.get(code, 'Global Pool')} [+{code}]\n"
        f"📞 <b>GENERATED TARGET:</b> <code>+{allocated_num}</code>\n\n"
        f"⏳ <i>System actively monitoring background servers for incoming OTP stream payload packets...</i>"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 Change Assigned Number", callback_data=f"change_num_{code}"),
        types.InlineKeyboardButton("🌍 Return to Country Pools", callback_data="back_to_pools")
    )
    bot.edit_message_text(text=msg_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_num_"))
def callback_change_number(call):
    code = call.data.split("_")[2]
    numbers = get_combo_numbers(code)
    if not numbers: return
    
    allocated_num = random.choice(numbers)
    save_user(call.from_user.id, country_code=code, assigned_number=allocated_num)
    
    msg_text = (
        f"🖥️ <b>SERVER STATUS:</b> UPDATED\n"
        f"📱 <b>PLATFORM PROTOCOL:</b> WhatsApp\n"
        f"🌍 <b>COUNTRY IDENTIFIER:</b> {country_codes.get(code, 'Global Pool')} [+{code}]\n"
        f"📞 <b>NEW TARGET LOGGED:</b> <code>+{allocated_num}</code>\n\n"
        f"⏳ <i>System actively monitoring background servers for incoming OTP stream payload packets...</i>"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 Change Assigned Number", callback_data=f"change_num_{code}"),
        types.InlineKeyboardButton("🌍 Return to Country Pools", callback_data="back_to_pools")
    )
    bot.edit_message_text(text=msg_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_pools")
def callback_back_to_pools(call):
    markup = create_country_selection_markup()
    bot.edit_message_text(text="🌍 <b>Select your desired Active Country Pool:</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "verify_sub")
def callback_verification_processor(call):
    if force_sub_check(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Identity subscription validated structure!", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_start_command(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Access Denied. Verify all channel links maps first!", show_alert=True)

# ------------------ ADMINISTRATIVE PORTAL ------------------
@bot.message_handler(func=lambda m: m.text == "🔐 Admin Portal")
def admin_portal_display(message):
    if message.from_user.id not in ADMIN_IDS: return
    
    m_mode = is_maintenance_mode()
    status_icon = "🔴 Maintenance Mode Active" if m_mode else "🟢 Operational System Live"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"⚙️ Toggle Status: {status_icon}", callback_data="toggle_m_mode"),
        types.InlineKeyboardButton("📥 Synchronize Pool Base Database (.txt)", callback_data="admin_upload"),
        types.InlineKeyboardButton("📢 Add Force Sub Target Link", callback_data="admin_add_force")
    )
    bot.send_message(message.chat.id, "⚡ <b>Control Center Core Management Protocol</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_m_mode")
def callback_toggle_maintenance(call):
    if call.from_user.id not in ADMIN_IDS: return
    current = is_maintenance_mode()
    new_state = "0" if current else "1"
    toggle_maintenance_mode(new_state)
    bot.answer_callback_query(call.id, "🔥 Operational parameters shifted successfully!", show_alert=True)
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_upload")
def admin_trigger_upload(call):
    if call.from_user.id not in ADMIN_IDS: return
    msg = bot.send_message(call.message.chat.id, "Enter target routing configuration Country Code (e.g. 92, 1, 7):")
    bot.register_next_step_handler(msg, process_admin_cc_step)

def process_admin_cc_step(message):
    cc = message.text.strip().replace("+", "")
    msg = bot.send_message(message.chat.id, f"Now upload raw context `.txt` number combo metrics for pool [+{cc}]:")
    bot.register_next_step_handler(msg, lambda m: save_admin_bulk_file(m, cc))

def save_admin_bulk_file(message, cc):
    if not message.document or not message.document.file_name.endswith('.txt'):
        bot.send_message(message.chat.id, "❌ File architecture error. Request dropped.")
        return
    try:
        f_info = bot.get_file(message.document.file_id)
        f_data = bot.download_file(f_info.file_path)
        numbers = [line.strip() for line in f_data.decode('utf-8').splitlines() if line.strip()]
        if not numbers:
            bot.send_message(message.chat.id, "❌ Parsed empty matrix mapping arrays.")
            return
        save_combo_numbers(cc, numbers)
        bot.send_message(message.chat.id, f"✅ Successfully integrated <b>{len(numbers)} entry numbers</b> directly into system pool reference table mapping [+{cc}]!", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Engine validation exception error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_force")
def admin_trigger_forcesub(call):
    if call.from_user.id not in ADMIN_IDS: return
    msg = bot.send_message(call.message.chat.id, "Provide custom full Telegram verification channel target url map:\n(e.g., https://t.me/panthernumbers)")
    bot.register_next_step_handler(msg, process_admin_fs_url)

def process_admin_fs_url(message):
    url = message.text.strip()
    msg = bot.send_message(message.chat.id, "Provide user button title description context string for display interface:\n(e.g., Join Official Number Updates Channel)")
    bot.register_next_step_handler(msg, lambda m: save_admin_fs_record(m, url))

def save_admin_fs_record(message, url):
    desc = message.text.strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)", (url, desc))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Verification dynamic route initialized correctly!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed data integration step: {e}")
    finally:
        conn.close()

# ------------------ MAIN BOOTSTRAP WORKER ENGINE ------------------
if __name__ == "__main__":
    api_thread = threading.Thread(target=main_api_processing_engine, daemon=True)
    api_thread.start()
    
    print("🚀 Background API Worker Engine Layer Running...")
    print("🤖 System Frontend Telebot Protocol Online With New Flags Configured.")
    
    while True:
        try:
            bot.infinity_polling(timeout=15, long_polling_timeout=5)
        except telebot.apihelper.ApiTelegramException as te:
            if te.error_code == 409:
                time.sleep(15)
            else:
                time.sleep(5)
        except Exception:
            time.sleep(5)


