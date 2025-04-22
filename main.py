import base64
import gzip
import json
import os
import time
import urllib.parse
from typing import Any, Dict

import httpx
from deepdiff import DeepDiff
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

UNCIV_BASE_URL = "https://uncivserver.xyz"
UNCIV_GAME_ID = str(os.getenv("UNCIV_GAME_ID"))
UNCIV_CHECK_INTERVAL = int(os.getenv("UNCIV_CHECK_INTERVAL", 25))
UNCIV_COUNTRIES = {}
for key, value in os.environ.items():
    if key.startswith("UNCIV_COUNTRY_"):
        country_name = key.replace("UNCIV_COUNTRY_", "")
        UNCIV_COUNTRIES[country_name.lower()] = value

TELEGRAM_BOT_TOKEN = str(os.getenv("TELEGRAM_BOT_TOKEN"))
TELEGRAM_CHAT_ID = str(os.getenv("TELEGRAM_CHAT_ID"))

OPENAI_BASE_URL = str(os.getenv("OPENAI_BASE_URL"))
OPENAI_API_KEY = str(os.getenv("GROQ_API_KEY"))
OPENAI_MODEL = str(os.getenv("OPENAI_MODEL"))

client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

last_turn = None
last_country = None
previous_game_state = None


def send_message(chat_id: str, text: str):
    return httpx.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote(text)}"
    )


def get_game_state() -> Dict[str, Any]:
    """Получает текущее состояние игры в формате JSON"""
    try:
        response = httpx.get(f"{UNCIV_BASE_URL}/files/{UNCIV_GAME_ID}", timeout=30.0)
        if response.status_code == 200:
            return json.loads(
                gzip.decompress(base64.b64decode(response.content)).decode("utf-8")
            )
        else:
            print(f"Error getting game data: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Exception while getting game state: {e}")
        return {}


def parse_tech_changes(diff):
    tech_changes = []
    for civ in diff.get("values_changed", {}):
        if "techsResearched" in civ:
            civ_name = civ.split("'civName': '")[1].split("'")[0]
            tech = diff["values_changed"][civ]["new_value"]
            tech_changes.append({"civilization": civ_name, "technology": tech})
    return tech_changes


def parse_diplomacy_changes(diff):
    diplomacy_changes = []
    for change in diff.get("values_changed", {}):
        if "diplomaticStatus" in change:
            parts = change.split("'")
            civ1 = parts[3]
            civ2 = parts[7]
            old_status = diff["values_changed"][change]["old_value"]
            new_status = diff["values_changed"][change]["new_value"]
            diplomacy_changes.append(
                {
                    "civilizations": [civ1, civ2],
                    "old_status": old_status,
                    "new_status": new_status,
                }
            )
    return diplomacy_changes


def compare_game_states(
    old_state: Dict[str, Any], new_state: Dict[str, Any]
) -> Dict[str, Any]:
    """Сравнивает два состояния игры и возвращает структурированные различия"""
    diff = DeepDiff(old_state, new_state, ignore_order=True, verbose_level=2)

    # Парсим военные изменения
    military_changes = []
    for change in diff.get("values_changed", {}):
        if "militaryUnit" in change:
            parts = change.split("[")
            civ = parts[2].split("]")[0].strip("'")
            unit_type = parts[4].split("]")[0].strip("'")
            military_changes.append(
                {
                    "civilization": civ,
                    "unit": unit_type,
                    "change": diff["values_changed"][change],
                }
            )

    # Парсим изменения городов
    city_changes = []
    for change in diff.get("iterable_item_added", {}):
        if "cities" in change:
            civ = change.split("'civName': '")[1].split("'")[0]
            city_data = diff["iterable_item_added"][change]
            city_changes.append(
                {
                    "civilization": civ,
                    "city_name": city_data.get("name"),
                    "action": "Основан" if city_data.get("foundingCiv") else "Захвачен",
                }
            )

    return {
        "military": military_changes,
        "cities": city_changes,
        "technologies": parse_tech_changes(diff),
        "diplomacy": parse_diplomacy_changes(diff),
    }


def get_turn_summary(diff_data: Dict[str, Any]) -> str:
    """Получает краткую сводку изменений от LLM"""
    prompt = f"""
    **Контекст:**
    Создай эпическую хронику событий между ходами на основе этих изменений:
    - Военные действия: {json.dumps(diff_data['military'], ensure_ascii=False)}
    - Города: {json.dumps(diff_data['cities'], ensure_ascii=False)}
    - Технологии: {json.dumps(diff_data['technologies'], ensure_ascii=False)}
    - Дипломатия: {json.dumps(diff_data['diplomacy'], ensure_ascii=False)}

    **Инструкции:**
    1. Используй только названия цивилизаций из списка: {list(UNCIV_COUNTRIES.keys())}
    2. Опиши события в стиле исторической хроники
    3. Не упоминай технические детали вроде JSON-путей
    4. Сфокусируйся на ключевых изменениях
    5. Максимальная длина: 5 предложений

    **Пример хорошего ответа:**
    "Ирокезы усилили оборону границ, разместив опытных Мохокских воинов. Испания завершила исследование конной езды, открыв путь к конным отрядам. У берегов Египта замечены первые триремы финикийцев."
        """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Ты историк, составляющий летопись цивилизаций. Превращай игровые события в эпические повествования.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        return response.choices[0].message.content or "No summary available"
    except Exception as e:
        print(f"Error getting summary from LLM: {e}")
        return "Failed to get changes summary due to error."


def check_game_status():
    """Проверяет статус игры и отправляет уведомления при изменениях"""
    global last_turn, last_country, previous_game_state

    try:
        current_game_state = get_game_state()

        if not current_game_state:
            print("Failed to get game state")
            return

        turn = current_game_state.get("turns")
        country_turn = current_game_state.get("currentPlayer")

        if last_turn != turn or last_country != country_turn:
            base_message = f"Ход #{turn}, ходит: {UNCIV_COUNTRIES.get(str(country_turn) if country_turn is not None else '', '')} ({country_turn})"

            if previous_game_state and last_turn != turn and last_turn is not None:
                diff_data = compare_game_states(previous_game_state, current_game_state)
                turn_summary = get_turn_summary(diff_data)

                send_message(TELEGRAM_CHAT_ID, base_message)
                send_message(TELEGRAM_CHAT_ID, f"📝 Сводка событий:\n\n{turn_summary}")
            else:
                send_message(TELEGRAM_CHAT_ID, base_message)

            last_turn = turn
            last_country = country_turn
            previous_game_state = current_game_state

    except Exception as e:
        print(f"Error checking game status: {e}")


if __name__ == "__main__":
    try:
        while True:
            check_game_status()
            time.sleep(UNCIV_CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Script stopped")
