"""Notify module — sends Telegram alerts on error."""
import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv
from requests import post

# Load credentials from ~/.hermes/.env
load_dotenv(Path.home() / '.hermes' / '.env')

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID   = os.getenv('TELEGRAM_CHAT_ID', '')


def send(text: str) -> dict | None:
    """Send a Telegram message. Returns response dict or None."""
    if not BOT_TOKEN or not CHAT_ID:
        print('[notify] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping')
        return None
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    try:
        r = post(url, data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}, timeout=15)
        return r.json()
    except Exception as e:
        print(f'[notify] Failed to send Telegram message: {e}')
        return None


def notify_error(script_name: str, error: Exception | str) -> None:
    """Send error alert to Telegram."""
    if isinstance(error, Exception):
        msg = str(error)
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        detail = f'\n\n```\n{tb[:500]}\n```'
    else:
        msg = error
        detail = ''

    send(f'❌ *{script_name} 失敗*\n\n`{msg}`{detail}')


def notify_ok(script_name: str, detail: str = '') -> None:
    """Send success message to Telegram."""
    text = f'✅ *{script_name} 完成*'
    if detail:
        text += f'\n\n{detail}'
    send(text)


if __name__ == '__main__':
    # Test
    send('🔔 *Hermes* notify.py 已就緒')
