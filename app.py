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

# ------------------ PANELS CONFIG ------------------
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
TELEGRAM_BOT_TOKEN = "8779005863:AAGdhmwCa75Usjd10JJHM8d6eaQ__g_DXNI"
TELEGRAM_GROUP_ID = "-1003867730992"
ADMIN_IDS = [7338805216]  # Locked Admin System ID
DB_PATH = "panther_bot_system.db"

# 3 Mandatory Links configuration
REQUIRED_CHANNELS = [
    {"url": "https://t.me/panthernumbers", "username": "@panthernumbers", "desc": "📱 Join Number Group"},
    {"url": "https://t.me/pantherotpgroup", "username": "@pantherotpgroup", "desc": "💬 Join OTP Group"},
    {"url": "https://t.me/meThod5527", "username": "@meThod5527", "desc": "✈️ Join Official Channel"}
]

# ------------------ MEMORY & SESSIONS ------------------
processed_ids = set()
xup_session = requests.Session()
xup_session.headers.update({"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ------------------ DATABASE SETUP ------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, first_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS combos (country_code TEXT PRIMARY KEY, numbers TEXT)''')
    conn.commit()
    conn.close()

init_db()

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

# ------------------ SUBSCRIPTION VERIFICATION ------------------
def force_sub_check(user_id):
    if user_id in ADMIN_IDS:
        return True
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel["username"], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception:
            return False
    return True

def force_sub_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for channel in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(text=channel["desc"], url=channel["url"]))
    markup.add(types.InlineKeyboardButton("✅ Checked & Joined", callback_data="verify_sub"))
    return markup

# ------------------ TELEGRAM SEND ------------------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✈️ Channel", "url": "https://t.me/meThod5527"},
                {"text": "📱 Number Channel", "url": "https://t.me/panthernumbers"}
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
        res = requests.post(url, data=payload, timeout=10)
        return res.status_code == 200
    except Exception:
        return False

# ------------------ GLOBAL COUNTRY DATABASE ------------------
country_codes = {
    "1": "🇺🇸 USA/Canada", "7": "🇷🇺 Russia", "20": "🇪🇬 Egypt", "27": "🇿🇦 South Africa",
    "30": "🇬🇷 Greece", "31": "🇳🇱 Netherlands", "32": "🇧🇪 Belgium", "33": "🇫🇷 France",
    "34": "🇪🇸 Spain", "36": "🇭🇺 Hungary", "39": "🇮🇹 Italy", "40": "🇷🇴 Romania",
    "41": "🇨🇭 Switzerland", "43": "🇦🇹 Austria", "44": "🇬🇧 United Kingdom", "45": "🇩🇰 Denmark",
    "46": "🇸🇪 Sweden", "47": "🇳🇴 Norway", "48": "🇵🇱 Poland", "49": "🇩🇪 Germany",
    "51": "🇵🇪 Peru", "52": "🇲🇽 Mexico", "53": "🇨🇺 Cuba", "54": "🇦🇷 Argentina",
    "55": "🇧🇷 Brazil", "56": "🇨🇱 Chile", "57": "🇨🇴 Colombia", "58": "🇻🇪 Venezuela",
    "60": "🇲🇾 Malaysia", "61": "🇦🇺 Australia", "62": "🇮🇩 Indonesia", "63": "🇵🇭 Philippines",
    "64": "🇳🇿 New Zealand", "65": "🇸🇬 Singapore", "66": "🇹🇭 Thailand", "81": "🇯🇵 Japan",
    "82": "🇰🇷 South Korea", "84": "🇻🇳 Vietnam", "86": "🇨🇳 China", "90": "🇹🇷 Turkey",
    "91": "🇮🇳 India", "92": "🇵🇰 Pakistan", "93": "🇦🇫 Afghanistan", "94": "🇱🇰 Sri Lanka",
    "95": "🇲🇲 Myanmar", "98": "🇮🇷 Iran", "211": "🇸🇸 South Sudan", "212": "🇲🇦 Morocco",
    "213": "🇩🇿 Algeria", "216": "🇹🇳 Tunisia", "218": "🇱🇾 Libya", "220": "🇬🇲 Gambia",
    "221": "🇸🇳 Senegal", "222": "🇲🇷 Mauritania", "223": "🇲🇱 Mali", "224": "🇬🇳 Guinea",
    "225": "🇨🇮 Ivory Coast", "226": "🇧開心 Burkina Faso", "227": "🇳🇪 Niger", "228": "🇹🇬 Togo",
    "229": "🇧🇯 Benin", "230": "🇲🇺 Mauritius", "231": "🇱🇷 Liberia", "232": "🇸🇱 Sierra Leone",
    "233": "🇬🇭 Ghana", "234": "🇳🇬 Nigeria", "235": "🇹🇩 Chad", "236": "🇨🇫 Central African Rep",
    "237": "🇨🇲 Cameroon", "238": "🇨🇻 Cape Verde", "239": "🇸🇹 Sao Tome", "240": "🇬🇶 Equatorial Guinea",
    "241": "🇬🇦 Gabon", "242": "🇨🇬 Congo", "243": "🇨🇩 DR Congo", "244": "🇦🇴 Angola",
    "245": "🇬🇼 Guinea-Bissau", "248": "🇸🇨 Seychelles", "249": "🇸🇩 Sudan", "250": "🇷🇼 Rwanda",
    "251": "🇪🇹 Ethiopia", "252": "🇸🇴 Somalia", "253": "🇩🇯 Djibouti", "254": "🇰🇪 Kenya",
    "255": "🇹🇿 Tanzania", "256": "🇺🇬 Uganda", "257": "🇧🇮 Burundi", "258": "🇲🇿 Mozambique",
    "260": "🇿🇲 Zambia", "261": "🇲🇬 Madagascar", "262": "🇷🇪 Reunion", "263": "🇿🇼 Zimbabwe",
    "264": "🇳🇦 Namibia", "265": "🇲 Malawi", "266": "🇱🇸 Lesotho", "267": "🇧🇼 Botswana",
    "268": "🇸🇿 Eswatini", "269": "🇰🇲 Comoros", "290": "🇸🇭 Saint Helena", "291": "🇪🇷 Eritrea",
    "297": "🇦🇼 Aruba", "298": "🇫🇴 Faroe Islands", "299": "🇬🇱 Greenland", "350": "🇬🇮 Gibraltar",
    "351": "🇵🇹 Portugal", "352": "🇱🇺 Luxembourg", "353": "🇮🇪 Ireland", "354": "🇮🇸 Iceland",
    "355": "🇦🇱 Albania", "356": "🇲🇹 Malta", "357": "🇨🇾 Cyprus", "358": "🇫🇮 Finland",
    "359": "🇧🇬 Bulgaria", "370": "🇱🇹 Lithuania", "371": "🇱🇻 Latvia", "372": "🇪🇪 Estonia",
    "373": "🇲🇩 Moldova", "374": "🇦🇲 Armenia", "375": "🇧🇾 Belarus", "376": "🇦🇩 Andorra",
    "377": "🇲🇨 Monaco", "378": "🇸🇲 San Marino", "380": "🇺🇦 Ukraine", "381": "🇷🇸 Serbia",
    "382": "🇲🇪 Montenegro", "383": "🇽🇰 Kosovo", "385": "🇭🇷 Croatia", "386": "🇸🇮 Slovenia",
    "387": "🇧🇦 Bosnia", "389": "🇲🇰 North Macedonia", "420": "🇨🇿 Czech Republic",
    "421": "🇸🇰 Slovakia", "423": "🇱🇮 Liechtenstein", "500": "🇫🇰 Falkland Islands",
    "501": "🇧🇿 Belize", "502": "🇬🇹 Guatemala", "503": "🇸🇻 El Salvador", "504": "🇭🇳 Honduras",
    "505": "🇳🇮 Nicaragua", "506": "🇨🇷 Costa Rica", "507": "🇵🇦 Panama", "509": "🇭🇹 Haiti",
    "590": "🇬🇵 Guadeloupe", "591": "🇧🇴 Bolivia", "592": "🇬🇾 Guyana", "593": "🇪🇨 Ecuador",
    "594": "🇬🇫 French Guiana", "595": "🇵🇾 Paraguay", "596": "🇲🇶 Martinique", "597": "🇸🇷 Suriname",
    "598": "🇺🇾 Uruguay", "599": "🇨🇼 Curacao", "670": "🇹🇱 Timor-Leste", "672": "🇳帶 Norfolk Island",
    "673": "🇧🇳 Brunei", "674": "🇳🇷 Nauru", "675": "🇵🇬 Papua New Guinea", "676": "🇹🇴 Tonga",
    "677": "🇸🇧 Solomon Islands", "678": "🇻🇺 Vanuatu", "679": "🇫🇯 Fiji", "680": "🇵🇼 Palau",
    "681": "🇼🇫 Wallis and Futuna", "682": "🇨🇰 Cook Islands", "683": "🇳🇺 Niue", "685": "🇼🇸 Samoa",
    "686": "🇰🇮 Kiribati", "687": "🇳🇨 New Caledonia", "688": "🇹🇻 Tuvalu", "689": "🇵🇫 French Polynesia",
    "690": "🇹🇰 Tokelau", "691": "🇫🇲 Micronesia", "692": "🇲🇭 Marshall Islands", "850": "🇰🇵 North Korea",
    "852": "🇭🇰 Hong Kong", "853": "🇲🇴 Macau", "855": "🇰🇭 Cambodia", "856": "🇱🇦 Laos",
    "880": "🇧🇩 Bangladesh", "886": "🇹🇼 Taiwan", "960": "🇲🇻 Maldives", "961": "🇱🇧 Lebanon",
    "962": "🇯🇴 Jordan", "963": "🇸🇾 Syria", "964": "🇮🇶 Iraq", "965": "🇰🇼 Kuwait",
    "966": "🇸🇦 Saudi Arabia", "967": "🇾🇪 Yemen", "968": "🇴🇲 Oman", "970": "🇵🇸 Palestine",
    "971": "🇦🇪 UAE", "972": "🇮🇱 Israel", "973": "🇧🇭 Bahrain", "974": "🇶🇦 Qatar",
    "975": "🇧🇹 Bhutan", "976": "🇲🇳 Mongolia", "977": "🇳🇵 Nepal", "992": "🇹🇯 Tajikistan",
    "993": "🇹🇲 Turkmenistan", "994": "🇦🇿 Azerbaijan", "995": "🇬🇪 Georgia", "996": "🇰🇬 Kyrgyzstan",
    "998": "🇺🇿 Uzbekistan"
}

def get_country(number):
    number = str(number).replace("+", "").strip()
    for code in sorted(country_codes, key=len, reverse=True):
        if number.startswith(code):
            return country_codes[code]
    return "🌍 Unknown"

def mask_number(number):
    number = str(number).replace("+", "").strip()
    if len(number) > 6:
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
<b> 𝗡𝗘𝗪 𝗢𝗧𝗣 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬 𝗥𝗘𝗖𝗘𝗜𝗩𝗘𝗗 🎉</b>

<blockquote>🕰 Time: {pkt_time}</blockquote>
<blockquote>🌍 Country: {country}</blockquote>
<blockquote>📞 Number: {masked}</blockquote>
<blockquote>🟢 Service: {service_name}</blockquote>
<blockquote>🔑 OTP: <code>{otp}</code></blockquote>

📩 Full Message:
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
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    user_id = message.from_user.id
    if not force_sub_check(user_id):
        bot.send_message(message.chat.id, 
            "⚠️ <b>Access Denied! Mandatory Subscription Required</b>\n\n"
            "You must join our mandatory servers to interact with this application.", 
            parse_mode="HTML", reply_markup=force_sub_markup())
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("📱 Get Number"))
    if user_id in ADMIN_IDS:
        markup.add(types.KeyboardButton("🔐 Admin Panel"))

    bot.send_message(message.chat.id, f"Hello {message.from_user.first_name}, Welcome to PANTHER Bot system engine.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📱 Get Number")
def user_allocate_number_pool(message):
    if not force_sub_check(message.from_user.id): return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT country_code FROM combos")
    active_pools = [r[0] for r in c.fetchall()]
    conn.close()

    buttons = [types.InlineKeyboardButton(f"{country_codes.get(code, '🌍 Pool')} [+{code}]", callback_data=f"pool_{code}") for code in active_pools]
    if not buttons:
        bot.send_message(message.chat.id, "❌ No data records available. Ask Admin to upload numbers pool database.")
        return
    markup.add(*buttons)
    bot.send_message(message.chat.id, "🌍 <b>Select your desired Active Country Pool:</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pool_"))
def trigger_pool_distribution(call):
    code = call.data.split("_")[1]
    numbers = get_combo_numbers(code)
    if not numbers:
        bot.send_message(call.message.chat.id, "❌ Pool base layer empty.")
        return
    allocated_num = random.choice(numbers)
    bot.send_message(call.message.chat.id, f"<b>📱 POOL NUMBER GENERATED:</b>\n\n<code>{allocated_num}</code>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "verify_sub")
def callback_verification_processor(call):
    if force_sub_check(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_start_command(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)

# ------------------ ADMIN FILE DATABASE SYSTEM ------------------
@bot.message_handler(func=lambda m: m.text == "🔐 Admin Panel")
def admin_portal_display(message):
    if message.from_user.id not in ADMIN_IDS: return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📥 Bulk Upload Numbers (.txt)", callback_data="admin_upload"))
    bot.send_message(message.chat.id, "⚡ <b>System Management Panel Mode</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_upload")
def admin_trigger_upload(call):
    if call.from_user.id not in ADMIN_IDS: return
    msg = bot.send_message(call.message.chat.id, "Please enter target Country Code (e.g., 92, 1, 91):")
    bot.register_next_step_handler(msg, process_admin_cc_step)

def process_admin_cc_step(message):
    cc = message.text.strip().replace("+", "")
    msg = bot.send_message(message.chat.id, f"Now send the `.txt` bulk file database containing numbers for [+{cc}]:")
    bot.register_next_step_handler(msg, lambda m: save_admin_bulk_file(m, cc))

def save_admin_bulk_file(message, cc):
    if not message.document or not message.document.file_name.endswith('.txt'):
        bot.send_message(message.chat.id, "❌ Error: Please send a valid plain text `.txt` database file matrix.")
        return
    try:
        f_info = bot.get_file(message.document.file_id)
        f_data = bot.download_file(f_info.file_path)
        numbers = [line.strip() for line in f_data.decode('utf-8').splitlines() if line.strip()]
        if not numbers:
            bot.send_message(message.chat.id, "❌ File context parsed empty.")
            return
        save_combo_numbers(cc, numbers)
        bot.send_message(message.chat.id, f"✅ Successfully synchronized <b>{len(numbers)} numbers</b> into country pool [+{cc}]!", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Engine file runtime error: {e}")

# ------------------ MAIN BOOTSTRAP THREAD SYSTEM ------------------
if __name__ == "__main__":
    # Launch API Loop Processor inside background asynchronous Worker Thread
    api_thread = threading.Thread(target=main_api_processing_engine, daemon=True)
    api_thread.start()
    
    print("🚀 Background Engine Loop Active & API Connections Monitored...")
    print("🤖 Telegram Front-End Bot Interface Initialized successfully.")
    bot.infinity_polling()

