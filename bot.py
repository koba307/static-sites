#!/usr/bin/env python3
"""
Telegram бот для управления сайтом.
- Изменение номера телефона (с нормализацией в формат +7 (***) ***-**-**)
- Обновление всех HTML страниц
- Запуск / перезапуск / остановка локального сервера
- Меню через inline кнопки

Токен: 8820587760:AAHnjFaHOnXGmKajJcvo2AuH3iYWx3-PN4U
"""

import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from typing import Optional, Dict

import requests

# === НАСТРОЙКИ ===
TOKEN = "8820587760:AAHnjFaHOnXGmKajJcvo2AuH3iYWx3-PN4U"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")
PID_FILE = os.path.join(PROJECT_DIR, "server.pid")

# Простое хранилище состояний пользователей (для ввода номера)
user_states: Dict[int, str] = {}  # chat_id -> state (например "waiting_phone")

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def normalize_phone(raw: str) -> Optional[str]:
    """Нормализует номер к формату +7 (***) ***-**-**"""
    if not raw:
        return None
    digits = ''.join(c for c in raw if c.isdigit())
    if not digits:
        return None
    if digits.startswith('8') and len(digits) >= 11:
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '7' + digits
    if len(digits) != 11 or not digits.startswith('7'):
        return None
    return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

def get_port() -> int:
    try:
        cfg = load_config()
        return int(cfg.get("port", 8000))
    except:
        return 8000

def get_current_phone() -> str:
    try:
        cfg = load_config()
        return cfg.get("phone_number", "+7 (913) 256-25-93")
    except:
        return "+7 (913) 256-25-93"

def make_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Простой обновляемый прогресс-бар."""
    if total == 0:
        return "▱" * width
    filled = int(width * current / total)
    return "▰" * filled + "▱" * (width - filled) + f" {current}/{total} ({int(100*current/total)}%)"

def apply_phone_change(new_phone: str) -> int:
    """Вызывает логику обновления из apply_config.py"""
    try:
        import sys
        sys.path.insert(0, PROJECT_DIR)
        from apply_config import apply_phone as apply_func, normalize_phone as norm_func
        normalized = norm_func(new_phone)
        if not normalized:
            return 0
        cfg = load_config()
        cfg["phone_number"] = normalized
        save_config(cfg)
        return apply_func(normalized)
    except Exception as e:
        print(f"Error in apply_phone_change: {e}")
        return _fallback_apply_phone(new_phone)

def _fallback_apply_phone(new_phone: str) -> int:
    """Простая замена если импорт не сработал"""
    normalized = normalize_phone(new_phone)
    if not normalized:
        return 0
    cfg = load_config()
    cfg["phone_number"] = normalized
    save_config(cfg)

    import glob
    count = 0
    pattern = re.compile(r'\+7\s*\(\s*\d{3}\s*\)\s*[\d-]{7,}', re.IGNORECASE)
    quoted = re.compile(r'"\s*\+7\s*\(\s*\d{3}\s*\)\s*[\d-]{7,}\s*"', re.IGNORECASE)

    for root, _, files in os.walk(PROJECT_DIR):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    original = content
                    content = pattern.sub(normalized, content)
                    content = quoted.sub(f'"{normalized}"', content)
                    if content != original:
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(content)
                        count += 1
                except:
                    pass
    return count

# === SERVER CONTROL ===

def get_server_pid() -> Optional[int]:
    try:
        with open(PID_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return None

def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def start_server() -> str:
    pid = get_server_pid()
    if pid and is_process_running(pid):
        return "Сервер уже запущен."

    port = get_port()
    try:
        proc = subprocess.Popen(
            ["python3", "-m", "http.server", str(port), "--bind", "127.0.0.1"],
            cwd=PROJECT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        return f"✅ Сервер запущен на порту {port} (PID {proc.pid})"
    except Exception as e:
        return f"❌ Ошибка запуска: {e}"

def stop_server() -> str:
    pid = get_server_pid()
    stopped = False

    if pid and is_process_running(pid):
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            stopped = True
        except:
            pass

    try:
        subprocess.run(["pkill", "-f", "http.server"], capture_output=True)
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        stopped = True
    except:
        pass

    return "⏹ Сервер остановлен." if stopped else "Сервер не был запущен."

def restart_server() -> str:
    stop_server()
    time.sleep(1)
    return start_server()

# === SITES (Surge) CONTROL (with live progress) ===

GOS_SLUGS = {
    "open-spotifycom-intl-f-artist",
    "music-yandex-ru-artist",
    "ru-pinteres-com-pin",
    "gosuslugi-login",
    "yandex-maps-ru",
}

SOURCE_MAP = {
    "city-geo": "city.html",
    "dance-scool": "dance_scool.html",
    "promo-code": "promocode.html",
    "footbal-ru": "football.html",
}

def _prepare_site_folder(slug: str):
    os.makedirs(slug, exist_ok=True)
    if slug in GOS_SLUGS:
        src = "gos.html"
    else:
        src = SOURCE_MAP.get(slug, "gos.html")
    if os.path.exists(src):
        shutil.copy(src, os.path.join(slug, "index.html"))

def deploy_all_sites_with_progress(chat_id: int, message_id: int):
    try:
        cfg = load_config()
        links = cfg.get("links", [])
        if not links:
            edit_message(chat_id, message_id, "❌ Нет ссылок в config.json")
            return

        total = len(links)

        edit_message(chat_id, message_id, "🔧 Применяем настройки из config.json...")
        try:
            subprocess.run(["python3", "apply_config.py"], cwd=PROJECT_DIR, capture_output=True, timeout=30)
        except Exception:
            pass

        for i, slug in enumerate(links, 1):
            bar = make_progress_bar(i, total)
            text = (
                f"🚀 <b>Деплой сайтов на Surge</b>\n\n"
                f"{bar}\n\n"
                f"Текущий: <b>{slug}</b>\n"
                f"Подготовка папки и деплой..."
            )
            edit_message(chat_id, message_id, text)

            _prepare_site_folder(slug)
            domain = f"{slug}.surge.sh"
            try:
                res = subprocess.run(
                    ["surge", slug, domain],
                    cwd=PROJECT_DIR,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            except Exception as e:
                pass

            text = (
                f"🚀 <b>Деплой сайтов на Surge</b>\n\n"
                f"{bar}\n\n"
                f"✅ Готово: <b>{slug}</b> → https://{domain}"
            )
            edit_message(chat_id, message_id, text)
            time.sleep(0.8)

        final_text = (
            "✅ <b>Деплой всех сайтов завершён!</b>\n\n"
            "Теперь используй кнопку «📋 Статусы ссылок» чтобы проверить.\n"
            "После деплоя может потребоваться 30-60 сек на прогрев CDN."
        )
        edit_message(chat_id, message_id, final_text, back_keyboard())

    except Exception as e:
        edit_message(chat_id, message_id, f"❌ Ошибка деплоя: {e}", back_keyboard())

def teardown_all_sites_with_progress(chat_id: int, message_id: int):
    try:
        cfg = load_config()
        links = cfg.get("links", [])
        if not links:
            edit_message(chat_id, message_id, "❌ Нет ссылок в config.json")
            return

        total = len(links)

        for i, slug in enumerate(links, 1):
            bar = make_progress_bar(i, total)
            domain = f"{slug}.surge.sh"
            text = (
                f"⏹ <b>Остановка сайтов на Surge</b>\n\n"
                f"{bar}\n\n"
                f"Текущий: <b>{slug}</b> → teardown {domain}"
            )
            edit_message(chat_id, message_id, text)

            try:
                subprocess.run(
                    ["surge", "teardown", domain],
                    cwd=PROJECT_DIR,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            except Exception:
                pass

            text = (
                f"⏹ <b>Остановка сайтов на Surge</b>\n\n"
                f"{bar}\n\n"
                f"✅ Удалено: <b>{slug}</b>"
            )
            edit_message(chat_id, message_id, text)
            time.sleep(0.6)

        final_text = "✅ <b>Teardown всех сайтов завершён.</b>\nСайты удалены с Surge."
        edit_message(chat_id, message_id, final_text, back_keyboard())

    except Exception as e:
        edit_message(chat_id, message_id, f"❌ Ошибка: {e}", back_keyboard())

def restart_all_sites_with_progress(chat_id: int, message_id: int):
    edit_message(chat_id, message_id, "🔄 Перезапуск: сначала остановка всех сайтов...")
    teardown_all_sites_with_progress(chat_id, message_id)

    send_message(chat_id, "🔄 Теперь начинаем деплой...")
    deploy_all_sites_with_progress(chat_id, message_id)

def list_links_status(chat_id: int):
    cfg = load_config()
    links = cfg.get("links", [])
    if not links:
        send_message(chat_id, "Нет ссылок в config.json")
        return

    lines = ["📋 <b>Актуальные ссылки и статусы:</b>\n"]
    for slug in links:
        url = f"https://{slug}.surge.sh"
        try:
            resp = requests.head(url, timeout=6, allow_redirects=True)
            if resp.status_code == 200:
                status = "✅ Live"
            else:
                status = f"⚠️ HTTP {resp.status_code}"
        except Exception:
            status = "❌ Недоступен / ошибка"

        lines.append(f"• {url} — {status}")

    text = "\n".join(lines)
    send_message(chat_id, text, back_keyboard())

# === TELEGRAM HELPERS ===

def send_message(chat_id: int, text: str, reply_markup: Optional[dict] = None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Send message error: {e}")
        return None

def delete_message(chat_id: int, message_id: int):
    url = f"{BASE_URL}/deleteMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "message_id": message_id}, timeout=5)
    except:
        pass

def send_temp_message(chat_id: int, text: str, reply_markup: Optional[dict] = None, delete_after: int = 6):
    resp = send_message(chat_id, text, reply_markup)
    if resp and resp.get("ok") and "result" in resp:
        msg_id = resp["result"]["message_id"]
        threading.Timer(delete_after, lambda: delete_message(chat_id, msg_id)).start()
    return resp

def answer_callback(callback_id: str, text: str = ""):
    url = f"{BASE_URL}/answerCallbackQuery"
    try:
        requests.post(url, json={"callback_query_id": callback_id, "text": text}, timeout=5)
    except:
        pass

def edit_message(chat_id: int, message_id: int, text: str, reply_markup: Optional[dict] = None):
    url = f"{BASE_URL}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Edit message error: {e}")

# === INLINE KEYBOARDS ===

def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📞 Изменить номер телефона", "callback_data": "change_phone"}],
            [{"text": "🖥️ Локальный сервер (preview)", "callback_data": "server_menu"}],
            [{"text": "🌐 Все сайты (Surge)", "callback_data": "sites_menu"}],
            [{"text": "📋 Показать текущие настройки", "callback_data": "show_config"}],
            [{"text": "🔄 Применить настройки ко всем страницам", "callback_data": "apply_config"}],
        ]
    }

def server_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "▶️ Запустить сервер", "callback_data": "server_start"}],
            [{"text": "🔄 Перезапустить сервер", "callback_data": "server_restart"}],
            [{"text": "⏹ Остановить сервер", "callback_data": "server_stop"}],
            [{"text": "🔙 Назад в меню", "callback_data": "back_to_main"}],
        ]
    }

def sites_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🚀 Deploy all sites", "callback_data": "sites_deploy"}],
            [{"text": "🔄 Restart all sites", "callback_data": "sites_restart"}],
            [{"text": "⏹ Teardown all sites", "callback_data": "sites_teardown"}],
            [{"text": "📋 Статусы всех ссылок", "callback_data": "list_statuses"}],
            [{"text": "🔙 Назад в меню", "callback_data": "back_to_main"}],
        ]
    }

def back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔙 Назад", "callback_data": "back_to_main"}]
        ]
    }

# === HANDLERS ===

def handle_start(chat_id: int, message_id: Optional[int] = None):
    text = (
        "🤖 <b>Панель управления сайтом</b>\n\n"
        f"Текущий номер: <code>{get_current_phone()}</code>\n\n"
        "Выберите действие:"
    )
    if message_id:
        edit_message(chat_id, message_id, text, main_menu_keyboard())
    else:
        send_message(chat_id, text, main_menu_keyboard())

def handle_callback(callback: dict):
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    data = callback["data"]
    callback_id = callback["id"]

    if data == "change_phone":
        user_states[chat_id] = "waiting_phone"
        edit_message(chat_id, message_id,
                     "📞 Введите новый номер телефона в любом формате (например 89132562593 или +7 913 256-25-93):",
                     back_keyboard())
        answer_callback(callback_id)

    elif data == "server_menu":
        edit_message(chat_id, message_id, "🖥️ Управление локальным сервером (preview всех сайтов):", server_menu_keyboard())
        answer_callback(callback_id)

    elif data == "server_start":
        result = start_server()
        send_temp_message(chat_id, result, delete_after=8)
        answer_callback(callback_id, "Запуск...")

    elif data == "server_restart":
        result = restart_server()
        send_temp_message(chat_id, result, delete_after=8)
        answer_callback(callback_id)

    elif data == "server_stop":
        result = stop_server()
        send_temp_message(chat_id, result, delete_after=8)
        answer_callback(callback_id)

    elif data == "sites_menu":
        edit_message(chat_id, message_id, "🌐 Управление всеми сайтами на Surge:\n\n(Deploy/Restart/Teardown с живым прогресс-баром)", sites_menu_keyboard())
        answer_callback(callback_id)

    elif data == "sites_deploy":
        answer_callback(callback_id)
        edit_message(chat_id, message_id, "🚀 Запуск деплоя всех сайтов с прогрессом...")
        deploy_all_sites_with_progress(chat_id, message_id)

    elif data == "sites_restart":
        answer_callback(callback_id)
        edit_message(chat_id, message_id, "🔄 Запуск перезапуска всех сайтов (teardown + deploy)...")
        restart_all_sites_with_progress(chat_id, message_id)

    elif data == "sites_teardown":
        answer_callback(callback_id)
        edit_message(chat_id, message_id, "⏹ Запуск остановки всех сайтов с прогрессом...")
        teardown_all_sites_with_progress(chat_id, message_id)

    elif data == "list_statuses":
        answer_callback(callback_id)
        list_links_status(chat_id)

    elif data == "show_config":
        cfg = load_config()
        phone = cfg.get("phone_number", "не указан")
        links = cfg.get("links", [])
        port = cfg.get("port", 8000)
        text = (
            f"📋 <b>Текущие настройки</b>\n\n"
            f"Номер телефона: <code>{phone}</code>\n"
            f"Порт сервера: <code>{port}</code>\n\n"
            f"Ссылки ({len(links)}):\n" + "\n".join([f"• {l}" for l in links])
        )
        send_message(chat_id, text, back_keyboard())
        answer_callback(callback_id)

    elif data == "apply_config":
        updated = apply_phone_change(get_current_phone())
        send_temp_message(chat_id, f"✅ Настройки применены. Обновлено файлов: {updated}", delete_after=8)
        answer_callback(callback_id)

    elif data == "back_to_main":
        handle_start(chat_id, message_id)

def handle_message(message: dict):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if chat_id not in user_states:
        if text == "/start":
            handle_start(chat_id)
        else:
            send_message(chat_id, "Используйте /start для открытия меню.")
        return

    state = user_states.pop(chat_id, None)

    if state == "waiting_phone":
        normalized = normalize_phone(text)
        if not normalized:
            send_message(chat_id, "❌ Не удалось распознать номер. Попробуйте ещё раз (например: 8 913 256 25 93)")
            user_states[chat_id] = "waiting_phone"
            return

        cfg = load_config()
        cfg["phone_number"] = normalized
        save_config(cfg)

        updated = apply_phone_change(normalized)

        send_temp_message(
            chat_id,
            f"✅ Номер обновлён на <code>{normalized}</code>\n"
            f"Обновлено файлов: {updated}\n\n"
            "Теперь запустите деплой на Surge, если нужно опубликовать изменения.",
            delete_after=8
        )
        handle_start(chat_id)

# === MAIN POLLING ===

def main():
    print("Бот запущен. Ожидание обновлений...")
    offset = 0

    while True:
        try:
            resp = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            data = resp.json()

            if not data.get("ok"):
                print("Ошибка от Telegram:", data)
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                if "callback_query" in update:
                    handle_callback(update["callback_query"])
                elif "message" in update:
                    handle_message(update["message"])

        except Exception as e:
            print(f"Ошибка polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()