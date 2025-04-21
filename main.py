import base64
import gzip
import json
import os
import time
import urllib.parse

import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GAME_ID = os.getenv("GAME_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
COUNTRIES = {
    "Iroquois": "@vladimirskyicentral7683",
    "Spain": "@Sanechka0300",
    "Nok": "@unleex",
    "Egypt": "@xpos587",
    "Israel": "@arapchonok",
}

last_turn = None
last_country = None


def check_game_status():
    global last_turn, last_country

    try:
        server_response = httpx.get(f"https://uncivserver.xyz/files/{GAME_ID}_Preview")
        print(server_response)
        data = json.loads(
            gzip.decompress(base64.b64decode(server_response.content)).decode("utf-8")
        )

        turn = data["turns"]
        country_turn = data["currentPlayer"]

        if last_turn != turn or last_country != country_turn:
            message = f"Ход #{turn}, ходит: {COUNTRIES[country_turn]}"
            httpx.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={urllib.parse.quote(message)}"
            )

            last_turn = turn
            last_country = country_turn
    except Exception as e:
        print(f"Error: {e}")


try:
    while True:
        check_game_status()
        time.sleep(60)
except KeyboardInterrupt:
    print("Script stopped")
