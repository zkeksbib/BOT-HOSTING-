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

    "51": "🇵🇪 Peru",
    "52": "🇲🇽 Mexico",
    "53": "🇨🇺 Cuba",
    "54": "🇦🇷 Argentina",
    "55": "🇧🇷 Brazil",
    "56": "🇨🇱 Chile",
    "57": "🇨🇴 Colombia",
    "58": "🇻🇪 Venezuela",

    "60": "🇲🇾 Malaysia",
    "61": "🇦🇺 Australia",
    "62": "🇮🇩 Indonesia",
    "63": "🇵🇭 Philippines",
    "64": "🇳🇿 New Zealand",
    "65": "🇸🇬 Singapore",
    "66": "🇹🇭 Thailand",

    "81": "🇯🇵 Japan",
    "82": "🇰🇷 South Korea",
    "84": "🇻🇳 Vietnam",
    "86": "🇨🇳 China",

    "90": "🇹🇷 Turkey",
    "91": "🇮🇳 India",
    "92": "🇵🇰 Pakistan",
    "93": "🇦🇫 Afghanistan",
    "94": "🇱🇰 Sri Lanka",
    "95": "🇲🇲 Myanmar",
    "98": "🇮🇷 Iran",

    "211": "🇸🇸 South Sudan",
    "212": "🇲🇦 Morocco",
    "213": "🇩🇿 Algeria",
    "216": "🇹🇳 Tunisia",
    "218": "🇱🇾 Libya",

    "220": "🇬🇲 Gambia",
    "221": "🇸🇳 Senegal",
    "222": "🇲🇷 Mauritania",
    "223": "🇲🇱 Mali",
    "224": "🇬🇳 Guinea",
    "225": "🇨🇮 Ivory Coast",
    "226": "🇧🇫 Burkina Faso",
    "227": "🇳🇪 Niger",
    "228": "🇹🇬 Togo",
    "229": "🇧🇯 Benin",

    "230": "🇲🇺 Mauritius",
    "231": "🇱🇷 Liberia",
    "232": "🇸🇱 Sierra Leone",
    "233": "🇬🇭 Ghana",
    "234": "🇳🇬 Nigeria",
    "235": "🇹🇩 Chad",
    "236": "🇨🇫 Central African Rep",
    "237": "🇨🇲 Cameroon",
    "238": "🇨🇻 Cape Verde",
    "239": "🇸🇹 Sao Tome",
    "240": "🇬🇶 Equatorial Guinea",
    "241": "🇬🇦 Gabon",
    "242": "🇨🇬 Congo",
    "243": "🇨🇩 DR Congo",
    "244": "🇦🇴 Angola",
    "245": "🇬🇼 Guinea-Bissau",

    "248": "🇸🇨 Seychelles",
    "249": "🇸🇩 Sudan",
    "250": "🇷🇼 Rwanda",
    "251": "🇪🇹 Ethiopia",
    "252": "🇸🇴 Somalia",
    "253": "🇩🇯 Djibouti",
    "254": "🇰🇪 Kenya",
    "255": "🇹🇿 Tanzania",
    "256": "🇺🇬 Uganda",
    "257": "🇧🇮 Burundi",
    "258": "🇲🇿 Mozambique",
    "260": "🇿🇲 Zambia",
    "261": "🇲🇬 Madagascar",
    "262": "🇷🇪 Reunion",
    "263": "🇿🇼 Zimbabwe",
    "264": "🇳🇦 Namibia",
    "265": "🇲🇼 Malawi",
    "266": "🇱🇸 Lesotho",
    "267": "🇧🇼 Botswana",
    "268": "🇸🇿 Eswatini",
    "269": "🇰🇲 Comoros",

    "350": "🇬🇮 Gibraltar",
    "351": "🇵🇹 Portugal",
    "352": "🇱🇺 Luxembourg",
    "353": "🇮🇪 Ireland",
    "354": "🇮🇸 Iceland",
    "355": "🇦🇱 Albania",
    "356": "🇲🇹 Malta",
    "357": "🇨🇾 Cyprus",
    "358": "🇫🇮 Finland",
    "359": "🇧🇬 Bulgaria",
    "370": "🇱🇹 Lithuania",
    "371": "🇱🇻 Latvia",
    "372": "🇪🇪 Estonia",
    "373": "🇲🇩 Moldova",
    "374": "🇦🇲 Armenia",
    "375": "🇧🇾 Belarus",
    "376": "🇦🇩 Andorra",
    "377": "🇲🇨 Monaco",
    "378": "🇸🇲 San Marino",
    "380": "🇺🇦 Ukraine",
    "381": "🇷🇸 Serbia",
    "382": "🇲🇪 Montenegro",
    "383": "🇽🇰 Kosovo",
    "385": "🇭🇷 Croatia",
    "386": "🇸🇮 Slovenia",
    "387": "🇧🇦 Bosnia",
    "389": "🇲🇰 North Macedonia",

    "420": "🇨🇿 Czech Republic",
    "421": "🇸🇰 Slovakia",
    "423": "🇱🇮 Liechtenstein",

    "500": "🇫🇰 Falkland Islands",
    "501": "🇧🇿 Belize",
    "502": "🇬🇹 Guatemala",
    "503": "🇸🇻 El Salvador",
    "504": "🇭🇳 Honduras",
    "505": "🇳🇮 Nicaragua",
    "506": "🇨🇷 Costa Rica",
    "507": "🇵🇦 Panama",
    "509": "🇭🇹 Haiti",

    "591": "🇧🇴 Bolivia",
    "592": "🇬🇾 Guyana",
    "593": "🇪🇨 Ecuador",
    "595": "🇵🇾 Paraguay",
    "597": "🇸🇷 Suriname",
    "598": "🇺🇾 Uruguay",

    "670": "🇹🇱 Timor-Leste",
    "673": "🇧🇳 Brunei",
    "674": "🇳🇷 Nauru",
    "675": "🇵🇬 Papua New Guinea",
    "676": "🇹🇴 Tonga",
    "677": "🇸🇧 Solomon Islands",
    "678": "🇻🇺 Vanuatu",
    "679": "🇫🇯 Fiji",
    "680": "🇵🇼 Palau",
    "685": "🇼🇸 Samoa",
    "686": "🇰🇮 Kiribati",
    "687": "🇳🇨 New Caledonia",
    "688": "🇹🇻 Tuvalu",
    "689": "🇵🇫 French Polynesia",
    "691": "🇫🇲 Micronesia",
    "692": "🇲🇭 Marshall Islands",

    "850": "🇰🇵 North Korea",
    "852": "🇭🇰 Hong Kong",
    "853": "🇲🇴 Macau",
    "855": "🇰🇭 Cambodia",
    "856": "🇱🇦 Laos",

    "960": "🇲🇻 Maldives",
    "961": "🇱🇧 Lebanon",
    "962": "🇯🇴 Jordan",
    "963": "🇸🇾 Syria",
    "964": "🇮🇶 Iraq",
    "965": "🇰🇼 Kuwait",
    "966": "🇸🇦 Saudi Arabia",
    "967": "🇾🇪 Yemen",
    "968": "🇴🇲 Oman",
    "970": "🇵🇸 Palestine",
    "971": "🇦🇪 UAE",
    "972": "🇮🇱 Israel",
    "973": "🇧🇭 Bahrain",
    "974": "🇶🇦 Qatar",
    "975": "🇧🇹 Bhutan",
    "976": "🇲🇳 Mongolia",
    "977": "🇳🇵 Nepal",

    "992": "🇹🇯 Tajikistan",
    "993": "🇹🇲 Turkmenistan",
    "994": "🇦🇿 Azerbaijan",
    "995": "🇬🇪 Georgia",
    "996": "🇰🇬 Kyrgyzstan",
    "998": "🇺🇿 Uzbekistan"
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