# Unciv Telegram Notifier

![License](https://img.shields.io/github/license/xpos587/unciv-notifier)

Бот для отслеживания ходов и событий в игре Unciv с отправкой уведомлений в Telegram.

## Описание

Unciv Telegram Notifier — это инструмент, который мониторит состояние игры Unciv на сервере и отправляет уведомления в Telegram-чат при изменении хода или других важных событиях. Бот использует LLM (языковую модель) для создания кратких и увлекательных сводок событий в стиле исторической хроники.

## Возможности

- 🎮 Отслеживание смены ходов и текущего игрока
- 🏙️ Мониторинг основания и захвата городов
- ⚔️ Отслеживание военных действий
- 🔬 Мониторинг исследования технологий
- 🤝 Отслеживание дипломатических отношений
- 📝 Генерация кратких сводок событий с помощью LLM

## Требования

- Python 3.12
- Telegram бот (токен)
- ID игры Unciv
- API-ключ для LLM (Groq или OpenAI)

## Переменные окружения

| Переменная             | Описание                       | Пример                                 |
| ---------------------- | ------------------------------ | -------------------------------------- |
| `UNCIV_GAME_ID`        | ID игры на сервере Unciv       | `bfea7ea7-9c98-45fb-a13f-60400f9e045d` |
| `UNCIV_CHECK_INTERVAL` | Интервал проверки в секундах   | `25`                                   |
| `TELEGRAM_BOT_TOKEN`   | Токен Telegram бота            | `1234567890:AA...-..._...TE`           |
| `TELEGRAM_CHAT_ID`     | ID чата для отправки сообщений | `-1002512791594`                       |
| `OPENAI_BASE_URL`      | URL API для LLM                | `https://api.groq.com/openai/v1`       |
| `GROQ_API_KEY`         | API-ключ для Groq              | `gsk_...`                              |
| `OPENAI_MODEL`         | Модель для генерации сводок    | `llama3-70b-8192`                      |

## Установка и запуск

### Через Podman/Docker

```bash
podman-compose up -d
```

или

```bash
docker-compose up -d
```

### Через Conda

```bash
conda env create -f environment.yaml
conda activate default
python main.py
```

### Вручную

```bash
pip install httpx python-dotenv deepdiff openai
python main.py
```

## Настройка игроков

В файле `main.py` можно настроить соответствие между цивилизациями в игре и Telegram-аккаунтами игроков:

```python
UNCIV_COUNTRIES = {
    "Iroquois": "@vladimirskyicentral7683",
    "Spain": "@Sanechka0300",
    "Nok": "@unleex",
    "Egypt": "@xpos587",
    "Israel": "@arapchonok",
}
```

## Пример уведомления

```
Ход #42, ходит: @xpos587 (Egypt)

📝 Сводка событий:

Египет расширил свои владения, основав новый город Мемфис на богатых ресурсами землях. Ирокезы завершили исследование Письменности, что позволит им развивать науку быстрее соперников. Испания и Нок заключили пакт о ненападении, укрепляя свои дипломатические связи.
```

## 📄 License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
