# -*- coding: utf-8 -*-

import requests
import time
import re
from datetime import datetime, timedelta

# ------------------ PANELS ------------------
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
        "api_url": "http://pscall.net/restapi/smsreport",
        "key": "SVFWRT1SS4RygI6Ag1FQSQ==",
        "params": {
            "start": 0,
            "length": 500
        }
    }

]

# ------------------ TELEGRAM ------------------
TELEGRAM_BOT_TOKEN = "8779005863:AAGdhmwCa75Usjd10JJHM8d6eaQ__g_DXNI"
TELEGRAM_GROUP_ID = "-1003867730992"

# ------------------ MEMORY ------------------
processed_ids = set()

# ------------------ TELEGRAM ------------------
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

    data = {
        "chat_id": TELEGRAM_GROUP_ID,
        "text": msg,
        "parse_mode": "HTML",
        "reply_markup": str(keyboard).replace("'", '"')
    }

    try:

        requests.post(url, data=data, timeout=10)

        return True

    except Exception as e:

        print(f"❌ TELEGRAM ERROR: {e}")

        return False

# ------------------ COUNTRY DATABASE ------------------
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
    "39": "🇮🇹 Italy",
    "44": "🇬🇧 UK",
    "49": "🇩🇪 Germany",
    "91": "🇮🇳 India",
    "92": "🇵🇰 Pakistan",
    "964": "🇮🇶 Iraq",
    "58": "🇻🇪 Venezuela",
    "996": "🇰🇬 Kyrgyzstan",
    "855": "🇰🇭 Cambodia",
    "967": "🇾🇪 Yemen",
    "213": "🇩🇿 Algeria",
    "254": "🇰🇪 Kenya"
}

def get_country(number):

    number = str(number).replace("+", "")

    for code in sorted(country_codes, key=len, reverse=True):

        if number.startswith(code):
            return country_codes[code]

    return "🌍 Unknown"

# ------------------ HELPERS ------------------
def mask_number(number):

    number = str(number).replace("+", "")

    if len(number) > 6:
        return "+" + number[:4] + "****" + number[-2:]

    return "+" + number

def is_recent(dt_string):

    try:

        msg_time = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")

        return datetime.now() - msg_time < timedelta(minutes=2)

    except:

        return False

def extract_otp(msg):

    match = re.search(r'\d{3}-\d{3}|\d{4,8}', msg)

    return match.group(0) if match else None

# ------------------ FORMAT MESSAGE ------------------
def format_message(phone, otp, message):

    message = message.replace("\\n", "\n").replace("nn", "\n")

    masked = mask_number(phone)

    country = get_country(phone)

    pkt_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
𝗡𝗘𝗪 𝗢𝗧𝗣 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬 𝗥𝗘𝗖𝗘𝗜𝗩𝗘𝗗 🎉

<blockquote>🕰 Time: {pkt_time}</blockquote>
<blockquote>🌍 Country: {country}</blockquote>
<blockquote>📞 Number: {masked}</blockquote>
<blockquote>🟢 Service: WhatsApp</blockquote>
<blockquote>🔑 OTP: <code>{otp}</code></blockquote>

📩 Full Message:

<blockquote>
{message}
</blockquote>
"""

# ------------------ FETCH ------------------
def fetch_sms(panel):

    try:

        params = {}

        # PSCALL
        if "key" in panel:

            params["key"] = panel["key"]

            if "params" in panel:
                params.update(panel["params"])

        # NORMAL PANELS
        else:

            params["token"] = panel["token"]
            params["records"] = 1000

        # HEADERS
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        # REQUEST
        res = requests.get(
            panel["api_url"],
            params=params,
            headers=headers,
            timeout=10
        )

        print("\033[95m━━━━━━━━━━━━━━━━━━━\033[0m")
        print(f"\033[92mSUCCESS\033[0m : \033[96mAPI CONNECTED\033[0m")
        print(f"\033[93mPANEL\033[0m : {panel['api_url']}")
        print("\033[95m━━━━━━━━━━━━━━━━━━━\033[0m")

        # SAFE JSON
        try:
            data = res.json()
        except:
            return []

        if isinstance(data, dict):

            # NORMAL FORMAT
            if "data" in data:
                return data.get("data", [])

            # OTHER FORMAT
            if "rows" in data:
                return data.get("rows", [])

        return []

    except Exception as e:

        print(f"❌ API ERROR: {e}")

        return []

# ------------------ START ------------------
print("🚀 BOT STARTED")

# ------------------ LOOP ------------------
while True:

    for panel in PANELS:

        entries = fetch_sms(panel)

        for entry in entries:

            msg = (
                entry.get("message")
                or entry.get("sms")
                or ""
            )

            phone = (
                entry.get("num")
                or entry.get("number")
                or ""
            )

            date = (
                entry.get("dt")
                or entry.get("dateadded")
                or ""
            )

            if not msg or not phone:
                continue

            uid = f"{phone}-{msg}-{date}"

            # DUPLICATE CHECK
            if uid in processed_ids:
                continue

            otp = extract_otp(msg)

            if not otp:

                processed_ids.add(uid)

                continue

            final_msg = format_message(
                phone,
                otp,
                msg
            )

            sent = send_telegram(final_msg)

            if sent:

                print("\033[95m━━━━━━━━━━━━━━━━━━━\033[0m")
                print(f"\033[92mSUCCESS\033[0m : \033[96m{otp}\033[0m")
                print(f"\033[93mSEND TELEGRAM\033[0m \033[92m✅\033[0m")
                print("\033[95m━━━━━━━━━━━━━━━━━━━\033[0m")

            processed_ids.add(uid)

    time.sleep(3)