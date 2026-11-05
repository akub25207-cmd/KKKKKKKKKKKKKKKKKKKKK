import asyncio
import logging
import re
import os
import base64
import json
import random
import uuid
import urllib.parse
from datetime import datetime, timedelta
from decimal import Decimal

import aiohttp
import aiosqlite
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery,
    LabeledPrice, PreCheckoutQuery, LinkPreviewOptions, BotCommand, MenuButtonCommands,
)
from aiohttp import web
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
SECOND_BOT_TOKEN = os.getenv("SECOND_BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
USERBOT_PHONE = os.getenv("USERBOT_PHONE")
ADMIN_IDS = [int(i.strip()) for i in os.getenv("ADMIN_IDS", "").split(",") if i.strip()]
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")
API_SECRET = os.getenv("API_SECRET", "super_secret_key_123")
TONCENTER_API_KEY = os.getenv("TONCENTER_API_KEY")

TON_WALLET = "UQBASapxMnOPXG716Lv1U1jlCUpSJQg82t_H00ryIVM6T-Uv"
USDT_CONTRACT = "0:b113a994b5024a16719f69139328eb759596c38a25f59028b146fecdc3621dfe"
USDT_CONTRACT_USERFRIENDLY = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

CHANNEL_ID = -1002839409663
CHANNEL_LINK = "https://t.me/+Zb9AutLfLZViZGEy"
SUPPORT_USERNAME = "swordSar"
RULES_LINK = "https://telegra.ph/PhysicHub--Pravila-polzovaniya-servisom-05-06"
REVIEWS_LINK = "https://t.me/repswordSar/89"
BOT_USERNAME = "PhysicHubFiz_Bot"
STARS_BOT_USERNAME = "StarsPaPhuchic_Bot"
GIFT_LINK = "https://t.me/swordSar?text=%D0%9F%D1%80%D0%B8%D0%B2%D0%B5%D1%82%2C%20%D1%85%D0%BE%D1%87%D1%83%20%D0%BF%D0%BE%D0%BF%D0%BE%D0%BB%D0%BD%D0%B8%D1%82%D1%8C%20%D0%B1%D0%B0%D0%BB%D0%B0%D0%BD%D1%81%20NFT%20%D0%BF%D0%BE%D0%B4%D0%B0%D1%80%D0%BA%D0%BE%D0%BC."

STARS_RATE = Decimal("0.71")
ITEMS_PER_PAGE = 20

PHOTO_MAIN = "https://iili.io/BQyyE22.jpg"
PHOTO_PROFILE = "https://iili.io/BZzNhN9.jpg"

DB_FILE = "bot_data.db"
JSON_FILE = "bot_data.json"

# ==================== КАСТОМНЫЕ ЭМОДЗИ ====================
EMOJI = {
    "buy_regular": "5197593559888318791",
    "buy_aged":    "5197634907538476361",
    "profile":     "5197598168388230433",
    "rules":       "5197546448392048146",
    "reviews":     "5197270556872822884",
    "top_up":      "5197389832409600546",
    "promo_code":  "5260426225599405269",
    "transfer":    "5197623512990241076",
    "referral":    "5197514334921576594",
    "support":     "5197578965589445500",
    "back":        "5370600834050570279",
    "gift":        "5321290348884946501",
    "crypto_bot":  "5361836987642815474",
    "gram":        "5280922999241859582",
    "usdt_ton":    "5924538275342586042",
    "stars":       "6005661956931850799",
    "prev":        "5370600834050570279",
    "next":        "5370886921822156731",
    "buy":         "5127792722056315704",
    "pay":         "5397793586261539543",
    "check_pay":   "6030808822946206127",
    "keeper":      "5424905554432631390",
    "join":        "5377599075237502153",
    "rub":         "5377746319601324795",
}

EMOJI_TEXT = {
    "welcome":     "5195033767969839232",
    "balance":     "5445353829304387411",
    "promo_ok":    "5206607081334906820",
    "gram_title":  "5427168083074628963",
    "address":     "5443127283898405358",
    "keeper":      "5424905554432631390",
    "gram_rate":   "5427168083074628963",
    "auto_check":  "5264919878082509254",
    "warning":     "5424818078833715060",
    "usdt_title":  "5197434882321567830",
    "usdt_rate":   "5193177581888755275",
    "hint":        "5458603043203327669",
    "disclaimer":  "5397782960512444700",
    "purchased":   "5251203410396458957",
    "phone":       "5467539229468793355",
    "country":     "5224450179368767019",
    "price":       "5287231198098117669",
    "enter_num":   "5303214794336125778",
    "cloud_pass":  "5307843983102204243",
    "congrats":    "5951892127481860949",
    "prize":       "5850323366476519158",
    "score":       "6037514847443227774",
    "banned":      "5240241223632954241",
    "error":       "5210952531676504517",
}

def e(key, fallback="⭐"):
    return f'<tg-emoji emoji-id="{EMOJI_TEXT[key]}">{fallback}</tg-emoji>'

def btn(text, emoji_key=None, style=None, **kw):
    args = {"text": text, **kw}
    if emoji_key and EMOJI.get(emoji_key):
        args["icon_custom_emoji_id"] = EMOJI[emoji_key]
    if style:
        args["style"] = style
    return InlineKeyboardButton(**args)

# ==================== БОТЫ ====================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
second_bot = Bot(token=SECOND_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

dp = Dispatcher(storage=MemoryStorage())
dp_second = Dispatcher(storage=MemoryStorage())
router = Router()
router_second = Router()
dp.include_router(router)
dp_second.include_router(router_second)

# ==================== SQLITE ====================
async def db_one(q, p=()):
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(q, p) as c:
            r = await c.fetchone()
            return dict(r) if r else None

async def db_all(q, p=()):
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(q, p) as c:
            return [dict(r) for r in await c.fetchall()]

async def db_exec(q, p=()):
    async with aiosqlite.connect(DB_FILE) as db:
        cur = await db.execute(q, p)
        await db.commit()
        return cur.lastrowid

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0,
            purchases INTEGER DEFAULT 0, referrer_id INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS accounts (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, country_name TEXT, country_flag TEXT,
            country_emoji_id TEXT, country_code TEXT, acc_type TEXT, price REAL,
            phone TEXT, password TEXT, has_session INTEGER DEFAULT 0, added_at TEXT, year INTEGER);
        CREATE TABLE IF NOT EXISTS sold_accounts (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, country_name TEXT, country_flag TEXT,
            country_emoji_id TEXT, country_code TEXT, acc_type TEXT, price REAL,
            phone TEXT, password TEXT, has_session INTEGER DEFAULT 0, added_at TEXT,
            year INTEGER, buyer_id INTEGER, sold_at TEXT);
        CREATE TABLE IF NOT EXISTS orders (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, buyer_id INTEGER,
            status TEXT, code TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS pending_payments (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL,
            invoice_id INTEGER, status TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS pending_deposits (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount_rub REAL,
            amount_crypto REAL, currency TEXT, code TEXT UNIQUE, status TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS processed_transactions (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, hash TEXT UNIQUE, code TEXT, processed_at TEXT);
        CREATE TABLE IF NOT EXISTS topup_history (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL,
            method TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS purchase_history (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, phone TEXT,
            country TEXT, price REAL, created_at TEXT);
        CREATE TABLE IF NOT EXISTS referrals (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            invited_user_id INTEGER, has_purchased INTEGER DEFAULT 0, reward_claimed INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS banned (
            user_id INTEGER PRIMARY KEY, banned_at TEXT);
        CREATE TABLE IF NOT EXISTS promocodes (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, amount REAL,
            activations INTEGER, created_at TEXT, exhausted_at TEXT);
        CREATE TABLE IF NOT EXISTS promo_activations (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, code TEXT,
            activated_at TEXT, UNIQUE(user_id, code));
        CREATE TABLE IF NOT EXISTS giveaways (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT, prize TEXT, total INTEGER,
            participants TEXT, message_ids TEXT, status TEXT, created_by INTEGER,
            created_at TEXT, finished_at TEXT, winner_id INTEGER, winner_score INTEGER, results TEXT);
        CREATE TABLE IF NOT EXISTS userbot_sessions (
            phone TEXT PRIMARY KEY, session_string TEXT, account_id INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS deposit_counter (
            id INTEGER PRIMARY KEY AUTOINCREMENT, value INTEGER DEFAULT 0);
        """)
        await db.commit()

async def tcount(name):
    r = await db_one(f"SELECT COUNT(*) as c FROM {name}")
    return r["c"] if r else 0

# ==================== МИГРАЦИЯ ====================
async def migrate_from_json():
    if not os.path.exists(JSON_FILE):
        return
    if await tcount("users") > 0:
        logging.info("DB уже содержит данные, миграция пропущена")
        try:
            os.rename(JSON_FILE, JSON_FILE + ".migrated")
        except Exception:
            pass
        return
    logging.info(f"Миграция {JSON_FILE} → {DB_FILE}...")
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as ex:
        logging.error(f"Ошибка чтения JSON: {ex}")
        return
    async with aiosqlite.connect(DB_FILE) as db:
        for _, u in data.get("users", {}).items():
            await db.execute("INSERT OR IGNORE INTO users (user_id, username, balance, purchases, referrer_id, created_at) VALUES (?,?,?,?,?,?)",
                             (u.get("user_id"), u.get("username"), u.get("balance", 0), u.get("purchases", 0), u.get("referrer_id"), u.get("created_at")))
        for k, a in data.get("accounts", {}).items():
            await db.execute("INSERT OR IGNORE INTO accounts (doc_id, country_name, country_flag, country_code, acc_type, price, phone, password, has_session, added_at, year) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, a.get("country_name"), a.get("country_flag"), a.get("country_code"), a.get("acc_type"), a.get("price"), a.get("phone"), a.get("password"), 1 if a.get("has_session") else 0, a.get("added_at"), a.get("year")))
        for k, a in data.get("sold_accounts", {}).items():
            await db.execute("INSERT OR IGNORE INTO sold_accounts (doc_id, country_name, country_flag, country_code, acc_type, price, phone, password, has_session, added_at, year, buyer_id, sold_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, a.get("country_name"), a.get("country_flag"), a.get("country_code"), a.get("acc_type"), a.get("price"), a.get("phone"), a.get("password"), 1 if a.get("has_session") else 0, a.get("added_at"), a.get("year"), a.get("buyer_id"), a.get("sold_at")))
        for k, o in data.get("orders", {}).items():
            await db.execute("INSERT OR IGNORE INTO orders (doc_id, phone, buyer_id, status, code, created_at) VALUES (?,?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, o.get("phone"), o.get("buyer_id"), o.get("status"), o.get("code"), o.get("created_at")))
        for k, p in data.get("pending_payments", {}).items():
            await db.execute("INSERT OR IGNORE INTO pending_payments (doc_id, user_id, amount, invoice_id, status, created_at) VALUES (?,?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, p.get("user_id"), p.get("amount"), p.get("invoice_id"), p.get("status"), p.get("created_at")))
        for k, p in data.get("pending_deposits", {}).items():
            await db.execute("INSERT OR IGNORE INTO pending_deposits (doc_id, user_id, amount_rub, amount_crypto, currency, code, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, p.get("user_id"), p.get("amount_rub"), p.get("amount_crypto"), p.get("currency"), p.get("code"), p.get("status"), p.get("created_at")))
        for k, t in data.get("processed_transactions", {}).items():
            await db.execute("INSERT OR IGNORE INTO processed_transactions (doc_id, hash, code, processed_at) VALUES (?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, t.get("hash"), t.get("code"), t.get("processed_at")))
        for k, t in data.get("topup_history", {}).items():
            await db.execute("INSERT OR IGNORE INTO topup_history (doc_id, user_id, amount, method, created_at) VALUES (?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, t.get("user_id"), t.get("amount"), t.get("method"), t.get("created_at")))
        for k, p in data.get("purchase_history", {}).items():
            await db.execute("INSERT OR IGNORE INTO purchase_history (doc_id, user_id, phone, country, price, created_at) VALUES (?,?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, p.get("user_id"), p.get("phone"), p.get("country"), p.get("price"), p.get("created_at")))
        for k, r in data.get("referrals", {}).items():
            await db.execute("INSERT OR IGNORE INTO referrals (doc_id, user_id, invited_user_id, has_purchased, reward_claimed) VALUES (?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, r.get("user_id"), r.get("invited_user_id"), 1 if r.get("has_purchased") else 0, 1 if r.get("reward_claimed") else 0))
        for k, b in data.get("banned", {}).items():
            await db.execute("INSERT OR IGNORE INTO banned (user_id, banned_at) VALUES (?,?)",
                             (b.get("user_id"), b.get("banned_at")))
        for k, p in data.get("promocodes", {}).items():
            await db.execute("INSERT OR IGNORE INTO promocodes (doc_id, code, amount, activations, created_at, exhausted_at) VALUES (?,?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, p.get("code"), p.get("amount"), p.get("activations", 0), p.get("created_at"), p.get("exhausted_at")))
        for k, g in data.get("giveaways", {}).items():
            await db.execute("INSERT OR IGNORE INTO giveaways (doc_id, prize, total, participants, message_ids, status, created_by, created_at, finished_at, winner_id, winner_score, results) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                             (int(k) if str(k).isdigit() else None, g.get("prize"), g.get("total"), json.dumps(g.get("participants", []), ensure_ascii=False), json.dumps(g.get("message_ids", {}), ensure_ascii=False), g.get("status"), g.get("created_by"), g.get("created_at"), g.get("finished_at"), g.get("winner_id"), g.get("winner_score"), json.dumps(g.get("results", {}), ensure_ascii=False)))
        for phone, sess in data.get("userbot_sessions", {}).items():
            if isinstance(sess, dict):
                await db.execute("INSERT OR IGNORE INTO userbot_sessions (phone, session_string, account_id, created_at) VALUES (?,?,?,?)",
                                 (phone, sess.get("session_string"), sess.get("account_id"), sess.get("created_at")))
        await db.commit()
    try:
        os.rename(JSON_FILE, JSON_FILE + ".migrated")
    except Exception:
        pass
    logging.info("Миграция завершена")

# ==================== РАНТАЙМ ====================
main_userbot = None
userbot_clients = {}
TON_WALLET_RAW = None

# ==================== УТИЛС ====================
def is_admin(uid):
    return uid in ADMIN_IDS

def format_price(p):
    return f"{Decimal(str(p)).quantize(Decimal('0.01'))} ₽"

async def get_user(uid):
    return await db_one("SELECT * FROM users WHERE user_id = ?", (uid,))

async def create_user_if_not(uid, username=None, ref=None):
    u = await get_user(uid)
    if not u:
        await db_exec("INSERT INTO users (user_id, username, balance, purchases, referrer_id, created_at) VALUES (?,?,?,?,?,?)",
                      (uid, username or "Неизвестный", 0.0, 0, ref, datetime.now().isoformat()))
        if ref and ref != uid:
            ex = await db_one("SELECT 1 FROM referrals WHERE user_id = ? AND invited_user_id = ?", (ref, uid))
            if not ex:
                await db_exec("INSERT INTO referrals (user_id, invited_user_id, has_purchased, reward_claimed) VALUES (?,?,?,?)", (ref, uid, 0, 0))
    else:
        await db_exec("UPDATE users SET username = ? WHERE user_id = ?", (username or u.get("username", "Неизвестный"), uid))

async def update_balance(uid, bal):
    await db_exec("UPDATE users SET balance = ? WHERE user_id = ?", (float(bal), uid))

async def get_referral_count(uid):
    r = await db_one("SELECT COUNT(*) as c FROM referrals WHERE user_id = ?", (uid,))
    return r["c"] if r else 0

async def has_deposit_last_21_days(uid, min_amt=100):
    cutoff = datetime.now() - timedelta(days=21)
    rows = await db_all("SELECT amount, created_at FROM topup_history WHERE user_id = ?", (uid,))
    total = 0.0
    for r in rows:
        try:
            amt = float(r.get("amount", 0))
            c = datetime.fromisoformat(r.get("created_at", "2000-01-01"))
            if c >= cutoff:
                total += amt
        except Exception:
            pass
    return total >= min_amt

def convert_address_to_raw(addr):
    try:
        if ":" in addr:
            return addr
        b = base64.urlsafe_b64decode(addr + "=" * (-len(addr) % 4))
        if len(b) >= 34:
            return f"0:{b[2:34].hex()}"
        return addr
    except Exception as ex:
        logging.error(f"addr convert: {ex}")
        return addr

def extract_comment(in_msg):
    try:
        mc = in_msg.get("message_content", {}) or {}
        dec = mc.get("decoded", {}) or {}
        for k in ("comment", "text", "value", "msg"):
            v = dec.get(k)
            if v and isinstance(v, str):
                return v.strip()
        body = dec.get("body") or mc.get("body")
        if body:
            try:
                pb = base64.b64decode(body)
                if pb[:4] == b"\x00\x00\x00\x00":
                    t = pb[4:].decode("utf-8", errors="ignore").strip()
                    if t:
                        return t
            except Exception:
                pass
        return mc.get("text") or in_msg.get("message") or ""
    except Exception:
        return ""

def extract_usdt_comment(tr):
    try:
        dfp = tr.get("decoded_forward_payload")
        if dfp:
            if isinstance(dfp, dict):
                for k in ("comment", "text", "value", "msg"):
                    v = dfp.get(k)
                    if v and isinstance(v, str):
                        return v.strip()
            elif isinstance(dfp, str):
                return dfp.strip()
        fp = tr.get("forward_payload")
        if fp:
            try:
                pb = base64.b64decode(fp)
                if pb[:4] == b"\x00\x00\x00\x00":
                    t = (pb[8:] if len(pb) >= 8 else pb[4:]).decode("utf-8", errors="ignore")
                    t = "".join(c for c in t if c.isprintable()).strip()
                    if t and all(c.isalnum() or c in "-_" for c in t):
                        return t
            except Exception:
                pass
        return tr.get("comment") or ""
    except Exception:
        return ""

# ==================== ЮЗЕРБОТЫ ====================
async def restore_userbots_from_db():
    rows = await db_all("SELECT * FROM userbot_sessions")
    logging.info(f"RESTORE: найдено {len(rows)} сессий")
    for s in rows:
        phone = s.get("phone")
        ss = s.get("session_string")
        acc_id = s.get("account_id")
        if not phone or not ss:
            continue
        try:
            cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
            await cl.connect()
            me = await asyncio.wait_for(cl.get_me(), timeout=10)
            if me is None:
                raise Exception("get_me None")

            @cl.on(events.NewMessage(from_users=777000))
            async def code_handler(event, _phone=phone, _acc_id=acc_id):
                text = event.message.text or ""
                m = re.search(r"\b(\d{5})\b", text)
                if not m:
                    return
                code = m.group(1)
                orders = await db_all("SELECT * FROM orders WHERE phone = ? AND status = 'ожидает_код'", (_phone,))
                if not orders:
                    return
                o = orders[0]
                await bot.send_message(o["buyer_id"], f"{e('enter_num','🔑')} Код: <code>{code}</code>")
                await db_exec("UPDATE orders SET status = 'завершен', code = ? WHERE doc_id = ?", (code, o["doc_id"]))
                acc = await db_one("SELECT * FROM accounts WHERE doc_id = ?", (_acc_id,))
                if acc and acc.get("password"):
                    await asyncio.sleep(1)
                    await bot.send_message(o["buyer_id"], f"{e('cloud_pass','🔐')} Облачный пароль: <code>{acc['password']}</code>")

            userbot_clients[phone] = {"client": cl, "account_id": acc_id, "awaiting_code": False}
            logging.info(f"RESTORE: {phone} восстановлен")
        except Exception as ex:
            logging.error(f"RESTORE {phone}: {ex}")
            await db_exec("DELETE FROM userbot_sessions WHERE phone = ?", (phone,))

async def save_userbot_session(phone, client, acc_id):
    try:
        ss = client.session.save()
        if await db_one("SELECT 1 FROM userbot_sessions WHERE phone = ?", (phone,)):
            await db_exec("UPDATE userbot_sessions SET session_string = ?, account_id = ? WHERE phone = ?", (ss, acc_id, phone))
        else:
            await db_exec("INSERT INTO userbot_sessions (phone, session_string, account_id, created_at) VALUES (?,?,?,?)",
                          (phone, ss, acc_id, datetime.now().isoformat()))
        logging.info(f"SAVE: сессия {phone} сохранена")
    except Exception as ex:
        logging.error(f"SAVE {phone}: {ex}")

async def start_main_userbot():
    global main_userbot
    try:
        main_userbot = TelegramClient(StringSession(), API_ID, API_HASH)
        await main_userbot.connect()
        if not await main_userbot.is_user_authorized():
            await main_userbot.send_code_request(USERBOT_PHONE)
            for aid in ADMIN_IDS:
                try:
                    await bot.send_message(aid, f"{e('cloud_pass','🔐')} <b>Регистрация юзербота</b>\n\nНомер: {USERBOT_PHONE}\nОтправь код подтверждения.")
                except Exception:
                    pass
            return False
        logging.info("Юзербот уже авторизован")
        return True
    except Exception as ex:
        logging.error(f"Main userbot error: {ex}")
        return False

async def login_userbot_with_code(code):
    global main_userbot
    try:
        await main_userbot.sign_in(USERBOT_PHONE, code)
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(aid, f"{e('auto_check','✅')} Юзербот авторизован")
            except Exception:
                pass
        return True
    except SessionPasswordNeededError:
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(aid, f"{e('warning','⚠️')} Нужен облачный пароль! Отправь /pass_main пароль")
            except Exception:
                pass
        return False
    except Exception as ex:
        logging.error(f"Login error: {ex}")
        return False

async def create_userbot_for_account(phone, account_id):
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
        userbot_clients[phone] = {"client": client, "account_id": account_id, "awaiting_code": True}

        @client.on(events.NewMessage(from_users=777000))
        async def code_handler(event):
            text = event.message.message or ""
            m = re.search(r"\b(\d{5})\b", text)
            if not m:
                return
            code = m.group(1)
            orders = await db_all("SELECT * FROM orders WHERE phone = ? AND status = 'ожидает_код'", (phone,))
            if not orders:
                return
            o = orders[0]
            await bot.send_message(o["buyer_id"], f"{e('enter_num','🔑')} Код: <code>{code}</code>")
            await db_exec("UPDATE orders SET status = 'завершен', code = ? WHERE doc_id = ?", (code, o["doc_id"]))
            acc = await db_one("SELECT * FROM accounts WHERE doc_id = ?", (account_id,))
            if acc and acc.get("password"):
                await asyncio.sleep(1)
                await bot.send_message(o["buyer_id"], f"{e('cloud_pass','🔐')} Облачный пароль: <code>{acc['password']}</code>")
        return client
    except Exception as ex:
        logging.error(f"Create userbot error: {ex}")
        return None

async def login_account_userbot(phone, code):
    if phone not in userbot_clients:
        return False
    client = userbot_clients[phone]["client"]
    try:
        await client.sign_in(phone, code)
        if userbot_clients[phone].get("pending_data"):
            d = userbot_clients[phone]["pending_data"]
            d["has_session"] = True
            cols = ", ".join(d.keys())
            phs = ", ".join("?" * len(d))
            acc_id = await db_exec(f"INSERT INTO accounts ({cols}) VALUES ({phs})", tuple(d.values()))
            userbot_clients[phone]["account_id"] = acc_id
            del userbot_clients[phone]["pending_data"]
            await save_userbot_session(phone, client, acc_id)
        elif userbot_clients[phone].get("account_id"):
            await db_exec("UPDATE accounts SET has_session = 1 WHERE doc_id = ?", (userbot_clients[phone]["account_id"],))
            await save_userbot_session(phone, client, userbot_clients[phone]["account_id"])
        userbot_clients[phone]["awaiting_code"] = False
        logging.info(f"Юзербот вошёл в {phone} (без пароля)")
        return True
    except SessionPasswordNeededError:
        password = None
        if userbot_clients[phone].get("pending_data"):
            password = userbot_clients[phone]["pending_data"].get("password")
        elif userbot_clients[phone].get("account_id"):
            acc = await db_one("SELECT * FROM accounts WHERE doc_id = ?", (userbot_clients[phone]["account_id"],))
            password = acc.get("password") if acc else None
        if password:
            try:
                await client.sign_in(password=password)
                if userbot_clients[phone].get("pending_data"):
                    d = userbot_clients[phone]["pending_data"]
                    d["has_session"] = True
                    cols = ", ".join(d.keys())
                    phs = ", ".join("?" * len(d))
                    acc_id = await db_exec(f"INSERT INTO accounts ({cols}) VALUES ({phs})", tuple(d.values()))
                    userbot_clients[phone]["account_id"] = acc_id
                    del userbot_clients[phone]["pending_data"]
                    await save_userbot_session(phone, client, acc_id)
                elif userbot_clients[phone].get("account_id"):
                    await db_exec("UPDATE accounts SET has_session = 1 WHERE doc_id = ?", (userbot_clients[phone]["account_id"],))
                    await save_userbot_session(phone, client, userbot_clients[phone]["account_id"])
                userbot_clients[phone]["awaiting_code"] = False
                logging.info(f"Юзербот вошёл в {phone} (с паролем)")
                return True
            except Exception as ex:
                logging.error(f"Password {phone}: {ex}")
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(aid, f"{e('cloud_pass','🔐')} <b>Нужен облачный пароль для {phone}!</b>\nОтправь: <code>/pass {phone} пароль</code>")
            except Exception:
                pass
        return False
    except Exception as ex:
        logging.error(f"Account login error: {ex}")
        if phone in userbot_clients:
            del userbot_clients[phone]
        return False

# ==================== ФОНОВЫЕ ====================
async def check_accounts_health():
    while True:
        try:
            await asyncio.sleep(60)
            accs = await db_all("SELECT * FROM accounts")
            for a in accs:
                ph = a.get("phone")
                if not ph:
                    continue
                if ph in userbot_clients and userbot_clients[ph].get("awaiting_code"):
                    continue
                if ph not in userbot_clients:
                    await db_exec("DELETE FROM accounts WHERE doc_id = ?", (a["doc_id"],))
                    await db_exec("DELETE FROM userbot_sessions WHERE phone = ?", (ph,))
                    for aid in ADMIN_IDS:
                        try:
                            await bot.send_message(aid, f"{e('warning','⚠️')} Аккаунт {ph} потерял доступ!\nУдалён из продажи автоматически.")
                        except Exception:
                            pass
                    continue
                cl = userbot_clients[ph]["client"]
                try:
                    await cl.connect()
                    me = await asyncio.wait_for(cl.get_me(), timeout=15)
                    if me is None:
                        raise Exception("None")
                except Exception as ex:
                    logging.warning(f"Аккаунт {ph} мёртв: {ex} → удаляю из продажи")
                    await db_exec("DELETE FROM accounts WHERE doc_id = ?", (a["doc_id"],))
                    await db_exec("DELETE FROM userbot_sessions WHERE phone = ?", (ph,))
                    try:
                        await cl.disconnect()
                    except Exception:
                        pass
                    userbot_clients.pop(ph, None)
                    for aid in ADMIN_IDS:
                        try:
                            await bot.send_message(aid, f"{e('warning','⚠️')} Аккаунт {ph} потерял доступ!\nУдалён из продажи автоматически.")
                        except Exception:
                            pass
        except Exception as ex:
            logging.error(f"Health check error: {ex}")

async def check_giveaways():
    while True:
        try:
            await asyncio.sleep(300)
            active = await db_all("SELECT * FROM giveaways WHERE status = 'active'")
            for g in active:
                parts = json.loads(g.get("participants") or "[]")
                if g.get("total", 0) > 0 and len(parts) >= g["total"]:
                    logging.info(f"GIVEAWAY AUTO-FINISH: id={g['doc_id']}, participants={len(parts)}/{g['total']}")
                    await run_giveaway(g["doc_id"])
        except Exception as ex:
            logging.error(f"check_giveaways error: {ex}")

async def check_ton_transactions():
    global TON_WALLET_RAW
    iteration = 0
    while True:
        try:
            iteration += 1
            await asyncio.sleep(15)
            if not TON_WALLET_RAW:
                TON_WALLET_RAW = convert_address_to_raw(TON_WALLET)
            headers = {"X-API-Key": TONCENTER_API_KEY}
            logging.info(f"=== ИТЕРАЦИЯ {iteration}: проверка транзакций ===")
            # GRAM
            try:
                url = f"https://toncenter.com/api/v3/transactions?account={TON_WALLET_RAW}&limit=100"
                async with aiohttp.ClientSession() as s:
                    async with s.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as r:
                        res = await r.json()
                transactions = res.get("transactions", [])
                logging.info(f"GRAM: получил {len(transactions)} транзакций")
                for tx in transactions:
                    h = tx.get("hash", "")
                    if not h:
                        continue
                    logging.info(f"GRAM tx hash={h[:20]}...")
                    if await db_one("SELECT 1 FROM processed_transactions WHERE hash = ?", (h,)):
                        continue
                    if not tx.get("success") or tx.get("bounced"):
                        continue
                    inm = tx.get("in_msg") or {}
                    if not inm:
                        continue
                    comment = extract_comment(inm)
                    rv = inm.get("value")
                    if not comment:
                        continue
                    logging.info(f"GRAM: comment='{comment}', value={rv}")
                    dep = await db_one("SELECT * FROM pending_deposits WHERE code = ?", (comment,))
                    logging.info(f"GRAM: заявка найдена={dep is not None}")
                    if not dep:
                        await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (h, comment, datetime.now().isoformat()))
                        continue
                    if dep["currency"] != "GRAM":
                        continue
                    try:
                        val = int(rv)
                    except Exception:
                        continue
                    gram = Decimal(val) / Decimal("1000000000")
                    need = Decimal(str(dep["amount_crypto"]))
                    if gram < Decimal("0.2"):
                        continue
                    if gram < need * Decimal("0.99"):
                        await db_exec("DELETE FROM pending_deposits WHERE code = ?", (comment,))
                        try:
                            await bot.send_message(dep["user_id"],
                                f"{e('error','❌')} <b>Недоплата!</b>\n\n"
                                f"Вы отправили: <code>{gram:.4f} GRAM</code>\n"
                                f"Нужно было: <code>{need:.4f} GRAM</code>\n\n"
                                f"Зачисление не выполнено. Обратитесь в поддержку.")
                        except Exception:
                            pass
                        await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (h, comment, datetime.now().isoformat()))
                        continue
                    u = await get_user(dep["user_id"])
                    if u:
                        await update_balance(dep["user_id"], u["balance"] + float(dep["amount_rub"]))
                        await db_exec("DELETE FROM pending_deposits WHERE code = ?", (comment,))
                        await db_exec("INSERT INTO topup_history (user_id, amount, method, created_at) VALUES (?,?,?,?)",
                                      (dep["user_id"], dep["amount_rub"], "GRAM", datetime.now().isoformat()))
                        await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (h, comment, datetime.now().isoformat()))
                        try:
                            await bot.send_message(dep["user_id"], f"{e('auto_check','✅')} Баланс пополнен на {format_price(dep['amount_rub'])} через GRAM!")
                        except Exception:
                            pass
                        logging.info(f"GRAM ЗАЧИСЛЕН АВТОМАТИЧЕСКИ: {comment}")
            except Exception as ex:
                logging.error(f"GRAM блок упал: {ex}")
            # USDT
            try:
                url = f"https://toncenter.com/api/v3/jetton/transfers?owner_address={TON_WALLET_RAW}&direction=in&limit=100"
                async with aiohttp.ClientSession() as s:
                    async with s.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as r:
                        res = await r.json()
                transfers = res.get("jetton_transfers", [])
                logging.info(f"USDT: получил {len(transfers)} переводов")
                for tr in transfers:
                    h = tr.get("transaction_hash", "")
                    if not h:
                        continue
                    logging.info(f"USDT tx hash={h[:20]}...")
                    if await db_one("SELECT 1 FROM processed_transactions WHERE hash = ?", (h,)):
                        continue
                    if (tr.get("jetton_master") or "").lower() != USDT_CONTRACT.lower():
                        continue
                    rv = tr.get("amount")
                    if rv is None:
                        continue
                    try:
                        amt = int(rv)
                    except Exception:
                        continue
                    usdt = Decimal(amt) / Decimal("1000000")
                    if usdt < Decimal("0.1"):
                        continue
                    comment = extract_usdt_comment(tr)
                    logging.info(f"USDT: comment='{comment}', amount={usdt}")
                    if not comment:
                        await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (h, "", datetime.now().isoformat()))
                        continue
                    dep = await db_one("SELECT * FROM pending_deposits WHERE code = ?", (comment,))
                    logging.info(f"USDT: заявка найдена={dep is not None}")
                    if not dep:
                        await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (h, comment, datetime.now().isoformat()))
                        continue
                    if dep["currency"] != "USDT":
                        continue
                    need = Decimal(str(dep["amount_crypto"]))
                    if usdt < need * Decimal("0.99"):
                        await db_exec("DELETE FROM pending_deposits WHERE code = ?", (comment,))
                        try:
                            await bot.send_message(dep["user_id"],
                                f"{e('error','❌')} <b>Недоплата!</b>\n\n"
                                f"Вы отправили: <code>{usdt:.4f} USDT</code>\n"
                                f"Нужно было: <code>{need:.4f} USDT</code>\n\n"
                                f"Зачисление не выполнено. Обратитесь в поддержку.")
                        except Exception:
                            pass
                        await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (h, comment, datetime.now().isoformat()))
                        continue
                    u = await get_user(dep["user_id"])
                    if u:
                        await update_balance(dep["user_id"], u["balance"] + float(dep["amount_rub"]))
                        await db_exec("DELETE FROM pending_deposits WHERE code = ?", (comment,))
                        await db_exec("INSERT INTO topup_history (user_id, amount, method, created_at) VALUES (?,?,?,?)",
                                      (dep["user_id"], dep["amount_rub"], "USDT (TON)", datetime.now().isoformat()))
                        await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (h, comment, datetime.now().isoformat()))
                        try:
                            await bot.send_message(dep["user_id"], f"{e('auto_check','✅')} Баланс пополнен на {format_price(dep['amount_rub'])} через USDT!")
                        except Exception:
                            pass
                        logging.info(f"USDT ЗАЧИСЛЕН АВТОМАТИЧЕСКИ: {comment}")
            except Exception as ex:
                logging.error(f"USDT блок упал: {ex}")
        except Exception as ex:
            logging.error(f"TON monitor error: {ex}")

# ==================== CRYPTO ====================
async def get_usdt_rate_from_crypto_bot():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://pay.crypt.bot/api/getExchangeRates", headers={"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}) as r:
                d = await r.json()
                if d.get("ok"):
                    for x in d["result"]:
                        if x["source"] == "USDT" and x["target"] == "RUB" and x["is_valid"]:
                            return Decimal("1") / Decimal(x["rate"])
        return Decimal("0.011")
    except Exception:
        return Decimal("0.011")

async def get_gram_rate():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://pay.crypt.bot/api/getExchangeRates", headers={"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}) as r:
                d = await r.json()
                if d.get("ok"):
                    for x in d["result"]:
                        if x["source"] == "TON" and x["target"] == "RUB" and x["is_valid"]:
                            return Decimal(x["rate"])
        return Decimal("120")
    except Exception:
        return Decimal("120")

async def get_usdt_ton_rate():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://pay.crypt.bot/api/getExchangeRates", headers={"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}) as r:
                d = await r.json()
                if d.get("ok"):
                    for x in d["result"]:
                        if x["source"] == "USDT" and x["target"] == "RUB" and x["is_valid"]:
                            return Decimal(x["rate"])
        return Decimal("95")
    except Exception:
        return Decimal("95")

def generate_deposit_code():
    return f"sword-{uuid.uuid4().hex[:10]}"

def create_tonkeeper_link(amount, comment, jetton=None):
    base = "https://app.tonkeeper.com/transfer/" + TON_WALLET
    if jetton is None:
        n = int(Decimal(str(amount)) * Decimal("1000000000"))
        return f"{base}?amount={n}&text={urllib.parse.quote(comment)}"
    u = int(Decimal(str(amount)) * Decimal("1000000"))
    return f"{base}?jetton={jetton}&amount={u}&text={urllib.parse.quote(comment)}"

async def create_crypto_invoice(amount_rub):
    try:
        r = await get_usdt_rate_from_crypto_bot()
        usd = (Decimal(str(amount_rub)) * r).quantize(Decimal("0.01"))
        if usd < Decimal("0.1"):
            usd = Decimal("0.1")
        async with aiohttp.ClientSession() as s:
            async with s.post("https://pay.crypt.bot/api/createInvoice", headers={"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}, json={"asset": "USDT", "amount": str(usd), "description": "Пополнение баланса", "expires_in": 1800}) as resp:
                d = await resp.json()
                if d.get("ok"):
                    return d["result"]["bot_invoice_url"], d["result"]["invoice_id"]
        return None, None
    except Exception:
        return None, None

async def check_crypto_payment(invoice_id):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post("https://pay.crypt.bot/api/getInvoices", headers={"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}, json={"invoice_ids": invoice_id}) as r:
                d = await r.json()
                logging.info(f"Ответ API getInvoices: {d}")
                if d.get("ok") and d["result"].get("items"):
                    return d["result"]["items"][0]
                return None
    except Exception as ex:
        logging.error(f"Exception: {ex}")
        return None

# ==================== КЛАВИАТУРЫ ====================
async def get_country_keyboard_page(acc_type, page=0):
    rows = await db_all("SELECT DISTINCT country_code FROM accounts WHERE acc_type = ?", (acc_type,))
    u = sorted([r["country_code"] for r in rows if r["country_code"]])
    if not u:
        return InlineKeyboardMarkup(inline_keyboard=[[btn("Назад", emoji_key="back", callback_data="main_menu")]])
    total_p = (len(u) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    pc = u[page * ITEMS_PER_PAGE:(page + 1) * ITEMS_PER_PAGE]
    kb_rows, buf = [], []
    for c in pc:
        acc = await db_one("SELECT country_name, country_flag FROM accounts WHERE country_code = ? LIMIT 1", (c,))
        if not acc:
            continue
        flag = acc.get("country_flag") or ""
        name = acc.get("country_name") or c
        btn_text = f"{flag} {name}".strip() if flag else name
        buf.append(InlineKeyboardButton(text=btn_text, callback_data=f"country_{acc_type}_{c}"))
        if len(buf) == 5:
            kb_rows.append(buf)
            buf = []
    if buf:
        kb_rows.append(buf)
    nav = []
    if page > 0:
        nav.append(btn("Назад", emoji_key="prev", callback_data=f"page_{acc_type}_{page-1}"))
    if page < total_p - 1:
        nav.append(btn("Вперёд", emoji_key="next", callback_data=f"page_{acc_type}_{page+1}"))
    if nav:
        kb_rows.append(nav)
    kb_rows.append([btn("Назад", emoji_key="back", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb_rows)

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить аккаунт", callback_data="admin_add"),
         InlineKeyboardButton(text="Остатки", callback_data="admin_stock")],
        [InlineKeyboardButton(text="Рассылка", callback_data="admin_broadcast"),
         InlineKeyboardButton(text="Пополнить юзеру", callback_data="admin_topup_user")],
        [InlineKeyboardButton(text="Рефералы", callback_data="admin_referrals"),
         InlineKeyboardButton(text="Бан юзера", callback_data="admin_ban")],
        [InlineKeyboardButton(text="Создать промокод", callback_data="admin_promo"),
         InlineKeyboardButton(text="Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="Розыгрыш", callback_data="admin_giveaway")],
        [btn("Назад", emoji_key="back", callback_data="main_menu")],
    ])

def main_menu_keyboard(uid):
    rows = [
        [btn("Купить аккаунт", emoji_key="buy_regular", style="danger", callback_data="buy_regular"),
         btn("Аккаунт с отлегой", emoji_key="buy_aged", style="danger", callback_data="buy_aged")],
        [btn("Мой профиль", emoji_key="profile", callback_data="profile")],
        [btn("Правила", emoji_key="rules", url=RULES_LINK),
         btn("Отзывы", emoji_key="reviews", url=REVIEWS_LINK)],
    ]
    if is_admin(uid):
        rows.append([InlineKeyboardButton(text="Админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def show_main_menu(uid):
    text = (
        f"{e('welcome','✈️')} <b>Добро пожаловать</b>\n\n"
        "<i>Чем мы лучше других сервисов</i>\n"
        "<blockquote>Моментальная выдача аккаунта.\n"
        "Большой ассортимент аккаунтов.\n"
        "Лучшее качество аккаунтов.</blockquote>"
    )
    preview = LinkPreviewOptions(url=PHOTO_MAIN, prefer_large_media=True, show_above_text=False)
    await bot.send_message(uid, text, reply_markup=main_menu_keyboard(uid), link_preview_options=preview)

async def get_years_keyboard(cc):
    rows = await db_all("SELECT DISTINCT year FROM accounts WHERE country_code = ? AND acc_type = 'отлега' AND year IS NOT NULL ORDER BY year DESC", (cc,))
    ys = [r["year"] for r in rows if r["year"] is not None]
    if not ys:
        return InlineKeyboardMarkup(inline_keyboard=[[btn("Назад", emoji_key="back", callback_data="page_отлега_0")]])
    kb_rows, buf = [], []
    for y in ys:
        buf.append(InlineKeyboardButton(text=str(y), callback_data=f"year_{cc}_{y}"))
        if len(buf) == 3:
            kb_rows.append(buf)
            buf = []
    if buf:
        kb_rows.append(buf)
    kb_rows.append([btn("Назад", emoji_key="back", callback_data="page_отлега_0")])
    return InlineKeyboardMarkup(inline_keyboard=kb_rows)

async def get_available_account(acc_type, cc, year=None):
    q = "SELECT * FROM accounts WHERE acc_type = ? AND country_code = ?"
    p = [acc_type, cc]
    if year is not None:
        q += " AND year = ?"
        p.append(int(year))
    return await db_one(q + " LIMIT 1", tuple(p))

# ==================== БАН ====================
async def is_banned(uid):
    return (await db_one("SELECT 1 FROM banned WHERE user_id = ?", (uid,))) is not None

async def check_ban_and_answer(message: Message):
    if await is_banned(message.from_user.id):
        await message.answer(f"{e('banned','🚫')} Ваш тикет закрыт.")
        return True
    return False

# ==================== /pass ====================
@router.message(Command("pass"))
async def set_password(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Формат: <code>/pass +79991234567 пароль</code>")
        return
    ph, pw = parts[1], parts[2]
    if ph not in userbot_clients:
        await message.answer(f"{e('error','❌')} Юзербот не найден для этого номера.")
        return
    cl = userbot_clients[ph]["client"]
    try:
        await cl.sign_in(password=pw)
        if userbot_clients[ph].get("pending_data"):
            d = userbot_clients[ph]["pending_data"]
            d["has_session"] = True
            d["password"] = pw
            cols = ", ".join(d.keys())
            phs = ", ".join("?" * len(d))
            acc_id = await db_exec(f"INSERT INTO accounts ({cols}) VALUES ({phs})", tuple(d.values()))
            userbot_clients[ph]["account_id"] = acc_id
            del userbot_clients[ph]["pending_data"]
            await save_userbot_session(ph, cl, acc_id)
        elif userbot_clients[ph].get("account_id"):
            await db_exec("UPDATE accounts SET has_session = 1, password = ? WHERE doc_id = ?", (pw, userbot_clients[ph]["account_id"]))
            await save_userbot_session(ph, cl, userbot_clients[ph]["account_id"])
        userbot_clients[ph]["awaiting_code"] = False
        await message.answer(f"{e('auto_check','✅')} Облачный пароль для {ph} принят! Аккаунт готов к продаже.")
    except Exception as ex:
        await message.answer(f"{e('error','❌')} Ошибка: {ex}")

# ==================== ОБРАБОТЧИК КОДОВ (5 цифр) ====================
@router.message(F.text.regexp(r"^\d{5}$"))
async def catch_code(message: Message):
    if not is_admin(message.from_user.id):
        return
    if await check_ban_and_answer(message):
        return
    code = message.text.strip()
    if main_userbot and not await main_userbot.is_user_authorized():
        if await login_userbot_with_code(code):
            await message.answer(f"{e('auto_check','✅')} Юзербот авторизован")
            return
    awaiting_phones = [p for p, d in userbot_clients.items() if d.get("awaiting_code")]
    if not awaiting_phones:
        return
    ph = awaiting_phones[0]
    if await login_account_userbot(ph, code):
        await message.answer(f"{e('auto_check','✅')} Вход для {ph} выполнен!")
    else:
        await message.answer(f"{e('error','❌')} Неверный код для {ph}. Попробуй ещё раз или отправь /pass {ph} пароль")

# ==================== /start ====================
def get_args(message: Message):
    if not message.text:
        return ""
    p = message.text.split(maxsplit=1)
    return p[1] if len(p) > 1 else ""

@router.message(CommandStart())
async def cmd_start(message: Message):
    if await check_ban_and_answer(message):
        return
    args = get_args(message)
    ref = None
    if args.startswith("ref_"):
        try:
            ref = int(args.replace("ref_", ""))
        except Exception:
            pass
    await create_user_if_not(message.from_user.id, message.from_user.username, ref)
    try:
        m = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
        if m.status in ("creator", "administrator", "member"):
            await show_main_menu(message.from_user.id)
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Подписаться", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="Проверить подписку", callback_data="check_sub", style="success")],
            ])
            preview = LinkPreviewOptions(url=PHOTO_MAIN, prefer_large_media=True, show_above_text=False)
            await bot.send_message(message.from_user.id, "<b>Для использования бота подпишитесь на канал!</b>", reply_markup=kb, link_preview_options=preview)
    except Exception as ex:
        logging.error(f"Start error: {ex}")
        await message.answer(f"{e('error','❌')} Ошибка: {ex}")

@router.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    try:
        m = await bot.get_chat_member(CHANNEL_ID, call.from_user.id)
        if m.status in ("creator", "administrator", "member"):
            try:
                await call.message.delete()
            except Exception:
                pass
            await show_main_menu(call.from_user.id)
        else:
            await call.answer("Вы не подписаны!", show_alert=True)
    except Exception:
        await call.answer("Ошибка!")
    await call.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_main(call: CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_main_menu(call.from_user.id)
    await call.answer()

@router.callback_query(F.data.startswith("page_"))
async def page_navigation(call: CallbackQuery):
    p = call.data.split("_")
    acc_type, page = p[1], int(p[2])
    kb = await get_country_keyboard_page(acc_type, page)
    title = "<b>Покупка аккаунта</b>\n\nВыберите страну:" if acc_type == "обычный" else "<b>Аккаунты с отлегой</b>\n\nВыберите страну:"
    try:
        await call.message.edit_text(title, reply_markup=kb)
    except Exception:
        await call.message.answer(title, reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "profile")
async def show_profile(call: CallbackQuery):
    try:
        u = await get_user(call.from_user.id)
        if not u:
            await call.answer("Вы не зарегистрированы. Напишите /start", show_alert=True)
            return
        balance = u.get("balance", 0)
        username = u.get("username", "Неизвестный")
        purchases = u.get("purchases", 0)
        text = (
            "Профиль\n"
            "——————————————————\n"
            f"Имя пользователя: @{username}\n"
            f"Идентификатор: {call.from_user.id}\n"
            "——————————————————\n"
            f"{e('balance','👛')} Баланс: {format_price(balance)}\n"
            f"Покупок: {purchases}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [btn("Пополнить баланс", emoji_key="top_up", style="danger", callback_data="top_up")],
            [btn("Промокод", emoji_key="promo_code", style="danger", callback_data="promo_code")],
            [btn("Перевести деньги", emoji_key="transfer", style="danger", callback_data="transfer_money")],
            [btn("Реф программа", emoji_key="referral", style="danger", callback_data="referral")],
            [btn("Поддержка", emoji_key="support", style="danger", url=f"https://t.me/{SUPPORT_USERNAME}")],
            [btn("Назад", emoji_key="back", callback_data="main_menu")],
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        preview = LinkPreviewOptions(url=PHOTO_PROFILE, prefer_large_media=True, show_above_text=False)
        await bot.send_message(call.from_user.id, text, reply_markup=kb, link_preview_options=preview)
        await call.answer()
    except Exception as ex:
        logging.error(f"Profile error: {ex}")
        await call.answer("Ошибка загрузки профиля", show_alert=True)

# ==================== ПРОМОКОД ====================
class PromoCode(StatesGroup):
    waiting_promo = State()

@router.callback_query(F.data == "promo_code")
async def promo_code_start(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "Введите промокод:")
    await state.set_state(PromoCode.waiting_promo)
    await call.answer()

@router.message(PromoCode.waiting_promo)
async def promo_code_check(message: Message, state: FSMContext):
    if await check_ban_and_answer(message):
        await state.clear()
        return
    code = message.text.strip().upper()
    p = await db_one("SELECT * FROM promocodes WHERE code = ?", (code,))
    if not p:
        await message.answer(f"{e('error','❌')} Промокод не найден.")
        await state.clear()
        return
    already = await db_one("SELECT 1 FROM promo_activations WHERE user_id = ? AND code = ?",
                           (message.from_user.id, code))
    if already:
        await message.answer(f"{e('error','❌')} Вы уже активировали этот промокод.")
        await state.clear()
        return
    if p.get("exhausted_at"):
        t = datetime.fromisoformat(p["exhausted_at"])
        if datetime.now() > t + timedelta(minutes=5):
            await db_exec("DELETE FROM promocodes WHERE code = ?", (code,))
            await message.answer(f"{e('error','❌')} Промокод уже недействителен.")
            await state.clear()
            return
        else:
            await message.answer(f"{e('error','❌')} Промокод уже использован.")
            await state.clear()
            return
    left = p.get("activations", 0)
    if left <= 0:
        await db_exec("UPDATE promocodes SET exhausted_at = ? WHERE code = ?", (datetime.now().isoformat(), code))
        await message.answer(f"{e('error','❌')} Промокод уже использован.")
        await state.clear()
        return
    amount = p["amount"]
    u = await get_user(message.from_user.id)
    await update_balance(message.from_user.id, u["balance"] + amount)
    await db_exec("INSERT OR IGNORE INTO promo_activations (user_id, code, activated_at) VALUES (?,?,?)",
                  (message.from_user.id, code, datetime.now().isoformat()))
    if left - 1 <= 0:
        await db_exec("UPDATE promocodes SET activations = 0, exhausted_at = ? WHERE code = ?", (datetime.now().isoformat(), code))
    else:
        await db_exec("UPDATE promocodes SET activations = ? WHERE code = ?", (left - 1, code))
    await message.answer(f"{e('promo_ok','✅')} Промокод активирован! На баланс зачислено {format_price(amount)}.")
    await state.clear()

# ==================== ПЕРЕВОД ====================
class TransferMoney(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()

@router.callback_query(F.data == "transfer_money")
async def transfer_money_start(call: CallbackQuery, state: FSMContext):
    u = await get_user(call.from_user.id)
    try:
        await call.message.delete()
    except Exception:
        pass
    text = (
        "<b>Перевод средств</b>\n\n"
        f"Доступно для перевода: {format_price(u.get('balance', 0))}\n\n"
        "Отправьте Telegram ID получателя (число).\n"
        "Узнать свой ID можно в профиле."
    )
    await bot.send_message(call.from_user.id, text)
    await state.set_state(TransferMoney.waiting_user_id)
    await call.answer()

@router.message(TransferMoney.waiting_user_id)
async def transfer_money_user_id(message: Message, state: FSMContext):
    if await check_ban_and_answer(message):
        await state.clear()
        return
    try:
        tid = int(message.text.strip())
    except Exception:
        await message.answer(f"{e('error','❌')} Введите корректный Telegram ID (число).")
        return
    if tid == message.from_user.id:
        await message.answer(f"{e('error','❌')} Нельзя переводить деньги самому себе.")
        await state.clear()
        return
    tu = await get_user(tid)
    if not tu:
        await message.answer(f"{e('error','❌')} Пользователь с таким ID не найден в боте.")
        await state.clear()
        return
    await state.update_data(target_id=tid)
    await message.answer(f"Введите сумму для перевода пользователю @{tu.get('username', tid)}:")
    await state.set_state(TransferMoney.waiting_amount)

@router.message(TransferMoney.waiting_amount)
async def transfer_money_amount(message: Message, state: FSMContext):
    if await check_ban_and_answer(message):
        await state.clear()
        return
    try:
        amt = float(message.text.replace(",", "."))
        if amt <= 0:
            await message.answer(f"{e('error','❌')} Сумма должна быть больше нуля.")
            return
    except Exception:
        await message.answer(f"{e('error','❌')} Введите корректную сумму.")
        return
    d = await state.get_data()
    tid = d["target_id"]
    sender = await get_user(message.from_user.id)
    recv = await get_user(tid)
    if sender["balance"] < amt:
        await message.answer(f"{e('error','❌')} Недостаточно средств на балансе.")
        await state.clear()
        return
    await update_balance(message.from_user.id, sender["balance"] - amt)
    await update_balance(tid, recv["balance"] + amt)
    await message.answer(f"{e('auto_check','✅')} Переведено {format_price(amt)} пользователю @{recv.get('username', tid)}.")
    try:
        await bot.send_message(tid, f"{e('auto_check','✅')} Вам перевели {format_price(amt)} от @{sender.get('username', message.from_user.id)}.")
    except Exception:
        pass
    await state.clear()

# ==================== РЕФЕРАЛКА ====================
@router.callback_query(F.data == "referral")
async def show_referral(call: CallbackQuery):
    cnt = await get_referral_count(call.from_user.id)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{call.from_user.id}"
    text = (
        "<b>Реферальная программа</b>\n\n"
        "<blockquote>Условия получения аккаунта: необходимо пригласить 15 уникальных пользователей. "
        "При условии, что один из приглашённых совершит покупку любого товара в боте, "
        "вы имеете право на получение любого аккаунта из ассортимента.</blockquote>\n\n"
        f"Ваша ссылка:\n<code>{link}</code>\n\n"
        f"Вы пригласили: <b>{cnt}</b> чел."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn("Назад", emoji_key="back", callback_data="profile")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, text, reply_markup=kb)
    await call.answer()

# ==================== ПОПОЛНЕНИЕ ====================
class TopUp(StatesGroup):
    waiting_crypto_amount = State()
    waiting_stars_amount = State()
    waiting_gram_amount = State()
    waiting_usdt_ton_amount = State()

@router.callback_query(F.data == "top_up")
async def top_up_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Подарками", emoji_key="gift", style="danger", url=GIFT_LINK),
         btn("Crypto Bot", emoji_key="crypto_bot", style="danger", callback_data="topup_crypto")],
        [btn("GRAM", emoji_key="gram", style="danger", callback_data="topup_gram"),
         btn("USDT (TON)", emoji_key="usdt_ton", style="danger", callback_data="topup_usdt_ton")],
        [btn("Звезды", emoji_key="stars", style="danger", callback_data="topup_stars")],
        [btn("Рублями (через админа)", emoji_key="rub", style="danger", callback_data="topup_admin_rub")],
        [btn("Назад", emoji_key="back", callback_data="profile")],
    ])
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "<b>Выберите способ пополнения:</b>", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "topup_admin_rub")
async def topup_admin_rub(call: CallbackQuery):
    text = (
        "<b>Пополнение рублями через админа</b>\n\n"
        "Нажмите кнопку ниже — откроется чат с админом с готовым сообщением.\n"
        "Укажите сумму, на которую хотите пополнить баланс."
    )
    admin_link = "https://t.me/swordSar?text=%D0%97%D0%B4%D0%B0%D1%80%D0%BE%D0%B2%D0%B0%20%2C%20%D1%85%D0%BE%D1%87%D1%83%20%D0%BF%D0%BE%D0%BF%D0%BE%D0%BB%D0%BD%D0%B8%D1%82%D1%8C%20%D0%B1%D0%B0%D0%BB%D0%B0%D0%BD%D1%81%20%D0%BD%D0%B0%20%D1%81%D1%83%D0%BC%D0%BC%D1%83"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Написать админу", emoji_key="support", style="danger", url=admin_link)],
        [btn("Назад", emoji_key="back", callback_data="top_up")],
    ])
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, text, reply_markup=kb)
    await call.answer()

# ---- CryptoBot ----
@router.callback_query(F.data == "topup_crypto")
async def crypto_amount(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "Введите сумму в рублях:")
    await state.set_state(TopUp.waiting_crypto_amount)
    await call.answer()

@router.message(TopUp.waiting_crypto_amount)
async def crypto_invoice(message: Message, state: FSMContext):
    if await check_ban_and_answer(message):
        await state.clear()
        return
    try:
        amt = Decimal(message.text.replace(",", "."))
        if amt < 10:
            await message.answer(f"{e('error','❌')} Минимальная сумма: 10 ₽")
            return
        await message.answer("Создаю счёт...")
        url, iid = await create_crypto_invoice(amt)
        if url:
            await db_exec("INSERT INTO pending_payments (user_id, amount, invoice_id, status, created_at) VALUES (?,?,?,?,?)",
                          (message.from_user.id, float(amt), iid, "pending", datetime.now().isoformat()))
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [btn("Оплатить", emoji_key="pay", url=url)],
                [btn("Проверить оплату", emoji_key="check_pay", callback_data=f"check_crypto_{iid}")],
                [btn("Назад", emoji_key="back", callback_data="top_up")],
            ])
            await message.answer(f"<b>Счёт на {format_price(amt)} создан!</b>", reply_markup=kb)
        else:
            await message.answer(f"{e('error','❌')} Не удалось создать счёт.")
    except Exception:
        await message.answer(f"{e('error','❌')} Введите корректную сумму!")
    await state.clear()

@router.callback_query(F.data.startswith("check_crypto_"))
async def check_crypto_payment_handler(call: CallbackQuery):
    iid = call.data.replace("check_crypto_", "")
    existing = await db_one("SELECT * FROM pending_payments WHERE invoice_id = ? AND status = 'paid'", (int(iid),))
    if existing:
        await call.answer("Этот счёт уже был зачислен ранее.", show_alert=True)
        return
    inv = await check_crypto_payment(iid)
    logging.info(f"Проверка платежа {iid}: {inv}")
    if not inv:
        await call.answer("Чек не найден в Crypto Bot. Возможно, истёк.", show_alert=True)
        return
    status = inv.get("status")
    if status == "paid":
        ausdt = float(inv.get("amount", 0))
        rate = await get_usdt_rate_from_crypto_bot()
        arub = float(Decimal(str(ausdt)) / rate) if rate else ausdt * 90
        u = await get_user(call.from_user.id)
        if u:
            await update_balance(call.from_user.id, u["balance"] + arub)
            await db_exec("INSERT INTO topup_history (user_id, amount, method, created_at) VALUES (?,?,?,?)",
                          (call.from_user.id, arub, "Crypto Bot", datetime.now().isoformat()))
            await db_exec("UPDATE pending_payments SET status = 'paid' WHERE invoice_id = ?", (int(iid),))
            try:
                await call.message.delete()
            except Exception:
                pass
            await bot.send_message(call.from_user.id, f"{e('auto_check','✅')} Баланс пополнен на {format_price(arub)}!")
            await call.answer("Оплата прошла!")
        else:
            await call.answer("Пользователь не найден!", show_alert=True)
    else:
        await call.answer(f"Статус: {status}. Оплата ещё не прошла.", show_alert=True)

# ---- GRAM ----
@router.callback_query(F.data == "topup_gram")
async def gram_start(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "Введите сумму в рублях для пополнения через GRAM:\n\nМинимум: 50 ₽")
    await state.set_state(TopUp.waiting_gram_amount)
    await call.answer()

@router.message(TopUp.waiting_gram_amount)
async def gram_invoice(message: Message, state: FSMContext):
    if await check_ban_and_answer(message):
        await state.clear()
        return
    try:
        arub = float(message.text)
        if arub < 50:
            await message.answer(f"{e('error','❌')} Минимальная сумма: 50 ₽")
            return
        gr = await get_gram_rate()
        agram = float(Decimal(str(arub)) / gr)
        if agram < 0.2:
            await message.answer(f"{e('error','❌')} Минимум 0.2 GRAM. По текущему курсу это ~{float(Decimal('0.2')*gr):.0f} ₽")
            return
        code = generate_deposit_code()
        await db_exec("INSERT INTO pending_deposits (user_id, amount_rub, amount_crypto, currency, code, status, created_at) VALUES (?,?,?,?,?,?,?)",
                      (message.from_user.id, arub, agram, "GRAM", code, "pending", datetime.now().isoformat()))
        keeper = create_tonkeeper_link(agram, code)
        text = (
            f"{e('gram_title','💎')} <b>Пополнение через GRAM</b>\n\n"
            f"Сумма: <code>{agram:.4f} GRAM</code>\n"
            f"Уникальный комментарий:\n<code>{code}</code>\n\n"
            f"{e('address','📤')} Адрес для перевода:\n<code>{TON_WALLET}</code>\n\n"
            f"{e('keeper','👛')} Кнопка «Открыть в Keeper» подставит адрес, сумму и комментарий.\n"
            f"После отправки нажмите «Проверить оплату» или дождитесь автопроверки.\n\n"
            f"{e('gram_rate','💰')} Курс: 1 GRAM = {gr:.2f} ₽\n"
            f"{e('auto_check','✅')} Бот дополнительно проверяет оплату каждые 15 секунд\n\n"
            f"{e('warning','⚠️')} <b>Важно:</b>\n"
            f"• Комментарий должен быть ТОЧНО: <code>{code}</code>\n"
            f"• Минимальная сумма: 0.2 GRAM\n"
            f"• После оплаты подождите 30 секунд"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [btn("Открыть в Keeper", emoji_key="keeper", url=keeper)],
            [btn("Проверить оплату", emoji_key="check_pay", callback_data=f"check_gram_{code}")],
        ])
        await message.answer(text, reply_markup=kb)
    except Exception:
        await message.answer(f"{e('error','❌')} Введите корректную сумму!")
    await state.clear()

@router.callback_query(F.data.startswith("check_gram_"))
async def check_gram_payment(call: CallbackQuery):
    global TON_WALLET_RAW
    code = call.data.replace("check_gram_", "")
    dep = await db_one("SELECT * FROM pending_deposits WHERE code = ?", (code,))
    if not dep:
        await call.answer("Платёж не найден!", show_alert=True)
        return
    if not TON_WALLET_RAW:
        TON_WALLET_RAW = convert_address_to_raw(TON_WALLET)
    try:
        url = f"https://toncenter.com/api/v3/transactions?account={TON_WALLET_RAW}&limit=50"
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"X-API-Key": TONCENTER_API_KEY}) as r:
                res = await r.json()
        found, txh = False, ""
        for tx in res.get("transactions", []):
            txh = tx.get("hash", "")
            if not txh or await db_one("SELECT 1 FROM processed_transactions WHERE hash = ?", (txh,)):
                continue
            inm = tx.get("in_msg") or {}
            cmt = extract_comment(inm)
            rv = inm.get("value")
            if rv is None:
                continue
            try:
                val = int(rv)
            except Exception:
                continue
            if cmt == code and val > 0:
                gram = Decimal(val) / Decimal("1000000000")
                if gram < Decimal("0.2"):
                    continue
                need = Decimal(str(dep["amount_crypto"]))
                if gram < need * Decimal("0.99"):
                    await db_exec("DELETE FROM pending_deposits WHERE code = ?", (code,))
                    await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (txh, code, datetime.now().isoformat()))
                    try:
                        await bot.send_message(dep["user_id"],
                            f"{e('error','❌')} <b>Недоплата!</b>\n\n"
                            f"Вы отправили: <code>{gram:.4f} GRAM</code>\n"
                            f"Нужно было: <code>{need:.4f} GRAM</code>\n\n"
                            f"Зачисление не выполнено. Обратитесь в поддержку.")
                    except Exception:
                        pass
                    await call.answer("Недоплата! Зачисление не выполнено.", show_alert=True)
                    return
                found = True
                break
        if found:
            u = await get_user(dep["user_id"])
            if u:
                await update_balance(dep["user_id"], u["balance"] + dep["amount_rub"])
                await db_exec("DELETE FROM pending_deposits WHERE code = ?", (code,))
                await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (txh, code, datetime.now().isoformat()))
                await db_exec("INSERT INTO topup_history (user_id, amount, method, created_at) VALUES (?,?,?,?)", (dep["user_id"], dep["amount_rub"], "GRAM", datetime.now().isoformat()))
                try:
                    await call.message.delete()
                except Exception:
                    pass
                await bot.send_message(call.from_user.id, f"{e('auto_check','✅')} Баланс пополнен на {format_price(dep['amount_rub'])}!")
                await call.answer("Оплата прошла!")
                return
        await call.answer("Перевод с указанным комментарием пока не найден.", show_alert=True)
    except Exception:
        await call.answer("Ошибка проверки. Попробуйте позже.", show_alert=True)

# ---- USDT ----
@router.callback_query(F.data == "topup_usdt_ton")
async def usdt_ton_start(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "Введите сумму в рублях для пополнения через USDT (TON):\n\nМинимум: 50 ₽")
    await state.set_state(TopUp.waiting_usdt_ton_amount)
    await call.answer()

@router.message(TopUp.waiting_usdt_ton_amount)
async def usdt_ton_invoice(message: Message, state: FSMContext):
    if await check_ban_and_answer(message):
        await state.clear()
        return
    try:
        arub = float(message.text)
        if arub < 50:
            await message.answer(f"{e('error','❌')} Минимальная сумма: 50 ₽")
            return
        ur = await get_usdt_ton_rate()
        ausdt = float(Decimal(str(arub)) / ur)
        if ausdt < 0.1:
            await message.answer(f"{e('error','❌')} Минимум 0.1 USDT. По текущему курсу это ~{float(Decimal('0.1')*ur):.0f} ₽")
            return
        code = generate_deposit_code()
        await db_exec("INSERT INTO pending_deposits (user_id, amount_rub, amount_crypto, currency, code, status, created_at) VALUES (?,?,?,?,?,?,?)",
                      (message.from_user.id, arub, ausdt, "USDT", code, "pending", datetime.now().isoformat()))
        keeper = create_tonkeeper_link(ausdt, code, jetton=USDT_CONTRACT_USERFRIENDLY)
        text = (
            f"{e('usdt_title','💵')} <b>Пополнение USDT в сети TON</b>\n\n"
            f"Сумма: <code>{ausdt:.4f} USDT</code>\n"
            f"Уникальный комментарий:\n<code>{code}</code>\n\n"
            f"{e('address','📤')} Адрес для перевода:\n<code>{TON_WALLET}</code>\n\n"
            f"{e('keeper','👛')} Кнопка «Открыть в Keeper» подставит все реквизиты.\n"
            f"Перед подтверждением проверьте, что выбран официальный USDT в сети TON, а не GRAM или другой токен.\n"
            f"Без точного комментария перевод не зачислится автоматически. Зачисляется фактически полученная сумма.\n\n"
            f"{e('usdt_rate','💰')} Курс: 1 USDT = {ur:.2f} ₽\n"
            f"{e('auto_check','✅')} Бот дополнительно проверяет оплату каждые 15 секунд\n\n"
            f"{e('warning','⚠️')} <b>Важно:</b>\n"
            f"• Комментарий должен быть ТОЧНО: <code>{code}</code>\n"
            f"• Минимальная сумма: 0.1 USDT\n"
            f"• После оплаты подождите 30 секунд"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [btn("Открыть в Keeper", emoji_key="keeper", url=keeper)],
            [btn("Проверить оплату", emoji_key="check_pay", callback_data=f"check_usdt_{code}")],
        ])
        await message.answer(text, reply_markup=kb)
    except Exception:
        await message.answer(f"{e('error','❌')} Введите корректную сумму!")
    await state.clear()

@router.callback_query(F.data.startswith("check_usdt_"))
async def check_usdt_payment(call: CallbackQuery):
    global TON_WALLET_RAW
    code = call.data.replace("check_usdt_", "")
    dep = await db_one("SELECT * FROM pending_deposits WHERE code = ?", (code,))
    if not dep:
        await call.answer("Платёж не найден!", show_alert=True)
        return
    if not TON_WALLET_RAW:
        TON_WALLET_RAW = convert_address_to_raw(TON_WALLET)
    try:
        url = f"https://toncenter.com/api/v3/jetton/transfers?owner_address={TON_WALLET_RAW}&direction=in&limit=50"
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"X-API-Key": TONCENTER_API_KEY}) as r:
                res = await r.json()
        found, txh = False, ""
        for tr in res.get("jetton_transfers", []):
            txh = tr.get("transaction_hash", "")
            if not txh or await db_one("SELECT 1 FROM processed_transactions WHERE hash = ?", (txh,)):
                continue
            if (tr.get("jetton_master") or "").lower() != USDT_CONTRACT.lower():
                continue
            cmt = extract_usdt_comment(tr)
            if not cmt:
                continue
            if cmt == code:
                try:
                    amt = int(tr.get("amount") or 0)
                except Exception:
                    continue
                usdt = Decimal(amt) / Decimal("1000000")
                if usdt < Decimal("0.1"):
                    continue
                need = Decimal(str(dep["amount_crypto"]))
                if usdt < need * Decimal("0.99"):
                    await db_exec("DELETE FROM pending_deposits WHERE code = ?", (code,))
                    await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (txh, code, datetime.now().isoformat()))
                    try:
                        await bot.send_message(dep["user_id"],
                            f"{e('error','❌')} <b>Недоплата!</b>\n\n"
                            f"Вы отправили: <code>{usdt:.4f} USDT</code>\n"
                            f"Нужно было: <code>{need:.4f} USDT</code>\n\n"
                            f"Зачисление не выполнено. Обратитесь в поддержку.")
                    except Exception:
                        pass
                    await call.answer("Недоплата! Зачисление не выполнено.", show_alert=True)
                    return
                found = True
                break
        if found:
            u = await get_user(dep["user_id"])
            if u:
                await update_balance(dep["user_id"], u["balance"] + dep["amount_rub"])
                await db_exec("DELETE FROM pending_deposits WHERE code = ?", (code,))
                await db_exec("INSERT OR IGNORE INTO processed_transactions (hash, code, processed_at) VALUES (?,?,?)", (txh, code, datetime.now().isoformat()))
                await db_exec("INSERT INTO topup_history (user_id, amount, method, created_at) VALUES (?,?,?,?)", (dep["user_id"], dep["amount_rub"], "USDT (TON)", datetime.now().isoformat()))
                try:
                    await call.message.delete()
                except Exception:
                    pass
                await bot.send_message(call.from_user.id, f"{e('auto_check','✅')} Баланс пополнен на {format_price(dep['amount_rub'])}!")
                await call.answer("Оплата прошла!")
                return
        await call.answer("Перевод USDT с вашим комментарием пока не найден.", show_alert=True)
    except Exception:
        await call.answer("Ошибка проверки. Попробуйте позже.", show_alert=True)

# ---- Stars ----
@router.callback_query(F.data == "topup_stars")
async def stars_amount(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    text = (
        "<b>Введите сумму в рублях для пополнения через Stars:</b>\n\n"
        f"{e('hint','💡')} Если у вас не хватает звёзд или их нет совсем — "
        f"вы можете купить их через нашего бота <b>@{STARS_BOT_USERNAME}</b>. "
        "И далее после покупки нужного количества звёзд "
        "вы можете пополнить свой баланс в боте.\n\n"
        f"{e('disclaimer','⚠️')} <blockquote>Мы не отвечаем за ваши действия и покупки "
        "у других продавцов. Мы отвечаем только за свой проект. "
        "Это лишь подсказка, где можно найти звёзды по низкой цене.</blockquote>"
    )
    await bot.send_message(call.from_user.id, text)
    await state.set_state(TopUp.waiting_stars_amount)
    await call.answer()

@router.message(TopUp.waiting_stars_amount)
async def stars_invoice(message: Message, state: FSMContext):
    if await check_ban_and_answer(message):
        await state.clear()
        return
    try:
        arub = float(message.text)
        if arub < 10:
            await message.answer(f"{e('error','❌')} Минимальная сумма: 10 руб.")
            return
        ai = int(arub)
        deep = f"https://t.me/{STARS_BOT_USERNAME}?start=inv_{message.from_user.id}_{ai}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [btn("Оплатить звёздами", emoji_key="stars", url=deep)],
            [btn("Назад", emoji_key="back", callback_data="top_up")],
        ])
        await message.answer(
            f"<b>Оплата через Telegram Stars</b>\n\n"
            f"<b>Сумма пополнения:</b> {format_price(arub)}\n\n"
            f"Нажмите кнопку ниже — откроется бот @{STARS_BOT_USERNAME} "
            f"с готовым счётом на оплату.\n\n"
            f"Оплата зачислится автоматически после подтверждения.",
            reply_markup=kb
        )
    except Exception as ex:
        await message.answer(f"{e('error','❌')} Ошибка: {ex}")
    await state.clear()

# ==================== 2-Й БОТ ====================
@router_second.message(CommandStart())
async def second_bot_start(message: Message):
    args = get_args(message)
    if args.startswith("inv_"):
        try:
            p = args.replace("inv_", "").split("_")
            uid = int(p[0])
            arub = float(p[1])
        except Exception:
            await message.answer("Ошибка в ссылке. Вернитесь в основной бот и попробуйте заново.")
            return
        if arub < 10:
            await message.answer(f"{e('error','❌')} Минимальная сумма: 10 ₽")
            return
        st = int(arub / float(STARS_RATE))
        await second_bot.send_invoice(
            chat_id=message.from_user.id,
            title="Пополнение баланса",
            description=f"Пополнение на {arub:.0f} ₽",
            payload=f"topup_{uid}_{arub}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Пополнение", amount=st)],
        )
    else:
        await message.answer(
            "Привет!\n\n"
            "Этот бот принимает оплату звёздами.\n\n"
            "Чтобы пополнить баланс — вернись в @PhysicHubFizi_Bot, "
            "выбери «Пополнить баланс» → «Звёзды» и нажми кнопку оплаты."
        )

@router_second.pre_checkout_query()
async def process_pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)

@router_second.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    p = payload.split("_")
    uid = int(p[1])
    arub = float(p[2])
    async with aiohttp.ClientSession() as s:
        try:
            async with s.post("http://localhost:8080/topup", json={"user_id": uid, "amount": arub, "secret": API_SECRET}) as r:
                res = await r.json()
                if res.get("status") == "ok":
                    await message.answer(f"{e('auto_check','✅')} Оплата получена! Баланс пополнен.")
                else:
                    await message.answer(f"{e('error','❌')} Ошибка: {res.get('message')}")
        except Exception as ex:
            await message.answer(f"{e('error','❌')} Ошибка связи: {ex}")

# ==================== ПОКУПКА ====================
@router.callback_query(F.data == "buy_regular")
async def buy_regular(call: CallbackQuery):
    kb = await get_country_keyboard_page("обычный", 0)
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "<b>Покупка аккаунта</b>\n\nВыберите страну:", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "buy_aged")
async def buy_aged(call: CallbackQuery):
    if not await db_all("SELECT 1 FROM accounts WHERE acc_type = 'отлега' LIMIT 1"):
        await call.answer("Нет доступных!", show_alert=True)
        return
    kb = await get_country_keyboard_page("отлега", 0)
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "<b>Аккаунты с отлегой</b>\n\nВыберите страну:", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("aged_country_"))
async def aged_country_select(call: CallbackQuery):
    cc = call.data.replace("aged_country_", "")
    kb = await get_years_keyboard(cc)
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "<b>Выберите год:</b>", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("country_"))
async def country_select(call: CallbackQuery):
    p = call.data.split("_", 2)
    if len(p) < 3:
        await call.answer("Ошибка", show_alert=True)
        return
    at, cc = p[1], p[2]
    acc = await get_available_account(at, cc)
    if not acc:
        await call.answer("Нет доступных!", show_alert=True)
        kb = await get_country_keyboard_page(at, 0)
        try:
            await call.message.edit_text("<b>Выберите страну:</b>", reply_markup=kb)
        except Exception:
            pass
        return
    yt = f" {acc['year']} года" if at == "отлега" and acc.get("year") else ""
    flag = acc.get("country_flag") or ""
    text = (
        f"<b>{'Обычный аккаунт' if at == 'обычный' else 'Аккаунт с отлегой'}{yt}</b>\n\n"
        f"{e('country','🌍')} Страна: {flag} {acc['country_name']}\n"
        f"{e('price','💰')} Цена: {format_price(acc['price'])}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Купить", emoji_key="buy", style="danger", callback_data=f"purchase_{acc['doc_id']}")],
        [btn("Назад", emoji_key="back", callback_data=f"page_{at}_0")],
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.delete()
        await bot.send_message(call.from_user.id, text, reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("year_"))
async def year_select(call: CallbackQuery):
    p = call.data.split("_", 2)
    if len(p) < 3:
        await call.answer("Ошибка", show_alert=True)
        return
    cc, y = p[1], p[2]
    acc = await get_available_account("отлега", cc, y)
    if not acc:
        await call.answer("Нет доступных!", show_alert=True)
        kb = await get_years_keyboard(cc)
        try:
            await call.message.edit_text("<b>Выберите год:</b>", reply_markup=kb)
        except Exception:
            pass
        return
    flag = acc.get("country_flag") or ""
    text = (
        f"<b>Аккаунт с отлегой {y} года</b>\n\n"
        f"{e('country','🌍')} Страна: {flag} {acc['country_name']}\n"
        f"Год: {y}\n"
        f"{e('price','💰')} Цена: {format_price(acc['price'])}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Купить", emoji_key="buy", style="danger", callback_data=f"purchase_{acc['doc_id']}")],
        [btn("Назад", emoji_key="back", callback_data=f"aged_country_{cc}")],
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.delete()
        await bot.send_message(call.from_user.id, text, reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("purchase_"))
async def purchase_account(call: CallbackQuery):
    aid = int(call.data.replace("purchase_", ""))
    acc = await db_one("SELECT * FROM accounts WHERE doc_id = ?", (aid,))
    u = await get_user(call.from_user.id)
    if not acc:
        await call.answer("Не найден!", show_alert=True)
        return
    if not u or u["balance"] < acc["price"]:
        await call.answer("Недостаточно средств!", show_alert=True)
        return
    await update_balance(call.from_user.id, u["balance"] - acc["price"])
    await db_exec("UPDATE users SET purchases = purchases + 1 WHERE user_id = ?", (call.from_user.id,))
    u2 = await get_user(call.from_user.id)
    if u2 and u2.get("referrer_id"):
        await db_exec("UPDATE referrals SET has_purchased = 1 WHERE user_id = ? AND invited_user_id = ?", (u2["referrer_id"], call.from_user.id))
    await db_exec("INSERT INTO purchase_history (user_id, phone, country, price, created_at) VALUES (?,?,?,?,?)",
                  (call.from_user.id, acc["phone"], acc["country_name"], acc["price"], datetime.now().isoformat()))
    await db_exec("INSERT INTO orders (phone, buyer_id, status, created_at) VALUES (?,?,?,?)",
                  (acc["phone"], call.from_user.id, "ожидает_код", datetime.now().isoformat()))
    await db_exec("INSERT INTO sold_accounts (country_name, country_flag, country_emoji_id, country_code, acc_type, price, phone, password, has_session, added_at, year, buyer_id, sold_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (acc["country_name"], acc["country_flag"], acc.get("country_emoji_id"), acc["country_code"], acc["acc_type"], acc["price"], acc["phone"], acc["password"], acc["has_session"], acc["added_at"], acc["year"], call.from_user.id, datetime.now().isoformat()))
    await db_exec("DELETE FROM accounts WHERE doc_id = ?", (aid,))
    try:
        await call.message.delete()
    except Exception:
        pass
    text = (
        f"{e('purchased','✅')} <b>Аккаунт куплен!</b>\n\n"
        f"{e('phone','📱')} Номер: <code>{acc['phone']}</code>\n"
        f"{e('country','🌍')} Страна: {acc['country_name']}\n"
        f"{e('price','💰')} Цена: {format_price(acc['price'])}\n\n"
        f"{e('enter_num','🔑')} <b>Введите номер в Telegram.</b>\nКод подтверждения придёт автоматически."
    )
    if acc.get("password"):
        text += f"\n\n{e('cloud_pass','🔐')} <b>Облачный пароль:</b> <code>{acc['password']}</code>"
    await bot.send_message(call.from_user.id, text)
    for aid_ in ADMIN_IDS:
        try:
            await bot.send_message(aid_, f"{e('price','💰')} Продан {acc['phone']}\n@{call.from_user.username}\n{format_price(acc['price'])}")
        except Exception:
            pass
    await call.answer("Куплен!")

# ==================== АДМИНКА ====================
class AddAccount(StatesGroup):
    waiting_country = State()
    waiting_type = State()
    waiting_year = State()
    waiting_price = State()
    waiting_phone = State()
    waiting_password = State()
    waiting_code = State()

class Broadcast(StatesGroup):
    waiting_text = State()

class BanUser(StatesGroup):
    waiting_ban_id = State()

class AdminTopup(StatesGroup):
    waiting_input = State()

class AdminPromo(StatesGroup):
    waiting_input = State()

class Giveaway(StatesGroup):
    waiting_prize = State()
    waiting_participants = State()

@router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа!", show_alert=True)
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "<b>Админ-панель</b>", reply_markup=admin_keyboard())
    await call.answer()

# ---- Add account ----
@router.callback_query(F.data == "admin_add")
async def admin_add_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "<b>Добавление аккаунта</b>\n\nВведите страну с флагом (например: 🇺🇸 США):")
    await state.set_state(AddAccount.waiting_country)
    await call.answer()

@router.message(AddAccount.waiting_country)
async def admin_add_country(message: Message, state: FSMContext):
    text = message.text or ""
    flag = ""
    name = text.strip()
    if len(name) >= 2 and ord(name[0]) > 127:
        flag = name[:2]
        name = name[2:].strip()
    await state.update_data(country=text, country_emoji_id=None, flag=flag, name=name or text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Обычный", callback_data="type_обычный"),
         InlineKeyboardButton(text="Отлега", callback_data="type_отлега")],
    ])
    await message.answer("Выберите тип:", reply_markup=kb)
    await state.set_state(AddAccount.waiting_type)

@router.callback_query(AddAccount.waiting_type, F.data.startswith("type_"))
async def admin_add_type(call: CallbackQuery, state: FSMContext):
    at = call.data.replace("type_", "")
    await state.update_data(acc_type=at)
    try:
        await call.message.delete()
    except Exception:
        pass
    if at == "отлега":
        await bot.send_message(call.from_user.id, "Введите год регистрации:")
        await state.set_state(AddAccount.waiting_year)
    else:
        await bot.send_message(call.from_user.id, "Введите цену в рублях:")
        await state.set_state(AddAccount.waiting_price)
    await call.answer()

@router.message(AddAccount.waiting_year)
async def admin_add_year(message: Message, state: FSMContext):
    try:
        y = int(message.text)
        await state.update_data(year=y)
        await message.answer("Введите цену в рублях:")
        await state.set_state(AddAccount.waiting_price)
    except Exception:
        await message.answer(f"{e('error','❌')} Введите год цифрами!")

@router.message(AddAccount.waiting_price)
async def admin_add_price(message: Message, state: FSMContext):
    try:
        pr = float(message.text.replace(",", "."))
        await state.update_data(price=pr)
        await message.answer("Введите номер телефона:")
        await state.set_state(AddAccount.waiting_phone)
    except Exception:
        await message.answer(f"{e('error','❌')} Введите цену цифрами!")

@router.message(AddAccount.waiting_phone)
async def admin_add_phone(message: Message, state: FSMContext):
    d = await state.get_data()
    ph = message.text.strip()
    await state.update_data(phone=ph)
    await message.answer("Введите облачный пароль (или напишите <b>нет</b> если его нет):")
    await state.set_state(AddAccount.waiting_password)

@router.message(AddAccount.waiting_password)
async def admin_add_password(message: Message, state: FSMContext):
    pw = message.text.strip()
    if pw.lower() == "нет":
        pw = None
    d = await state.get_data()
    await state.update_data(password=pw)
    ph = d["phone"]
    try:
        cl = TelegramClient(StringSession(), API_ID, API_HASH)
        await cl.connect()
        if not await cl.is_user_authorized():
            await cl.send_code_request(ph)
        userbot_clients[ph] = {
            "client": cl,
            "account_id": None,
            "awaiting_code": True,
            "pending_data": {
                "country_name": d["name"],
                "country_flag": d["flag"],
                "country_emoji_id": None,
                "country_code": d["name"],
                "acc_type": d["acc_type"],
                "price": d["price"],
                "phone": ph,
                "password": pw,
                "has_session": False,
                "added_at": datetime.now().isoformat(),
                "year": d.get("year"),
            }
        }

        @cl.on(events.NewMessage(from_users=777000))
        async def code_handler(event, _phone=ph):
            try:
                mt = event.message.message or ""
                m = re.search(r"\b(\d{5})\b", mt)
                if not m:
                    return
                code = m.group(1)
                orders = await db_all("SELECT * FROM orders WHERE phone = ? AND status = 'ожидает_код'", (_phone,))
                if not orders:
                    return
                o = orders[0]
                await bot.send_message(o["buyer_id"], f"{e('enter_num','🔑')} Код: <code>{code}</code>")
                await db_exec("UPDATE orders SET status = 'завершен', code = ? WHERE doc_id = ?", (code, o["doc_id"]))
                acc = await db_one("SELECT * FROM accounts WHERE phone = ?", (_phone,))
                if acc and acc.get("password"):
                    await asyncio.sleep(1)
                    await bot.send_message(o["buyer_id"], f"{e('cloud_pass','🔐')} Облачный пароль: <code>{acc['password']}</code>")
            except Exception as ex:
                logging.error(f"code_handler {_phone}: {ex}")

        await message.answer(f"{e('phone','📱')} Номер: {ph}\n{e('enter_num','🔑')} Введи код подтверждения:")
    except Exception as ex:
        await message.answer(f"{e('error','❌')} Ошибка отправки кода: {ex}")
        await state.clear()
        return
    await state.set_state(AddAccount.waiting_code)

@router.message(AddAccount.waiting_code)
async def admin_add_code(message: Message, state: FSMContext):
    d = await state.get_data()
    ph = d["phone"]
    code = message.text.strip()
    if await login_account_userbot(ph, code):
        await message.answer(
            f"{e('auto_check','✅')} Аккаунт {ph} готов!\n"
            f"Тип: {d.get('acc_type','')}\n"
            f"Цена: {format_price(d.get('price', 0))}"
            + (f"\nПароль: {d.get('password','нет')}" if d.get("password") else "")
        )
        await state.clear()
    else:
        await message.answer(f"{e('error','❌')} Неверный код. Попробуй ещё раз или отправь /pass {ph} пароль")

# ---- Stock ----
@router.callback_query(F.data == "admin_stock")
async def admin_stock(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = await db_all("SELECT * FROM accounts")
    text = "<b>Остатки:</b>\n\n"
    if not rows:
        text += "Нет доступных."
    else:
        cc = {}
        for a in rows:
            c = a["country_name"]
            if c not in cc:
                cc[c] = {"reg": 0, "aged": 0, "flag": a.get("country_flag") or ""}
            if a["acc_type"] == "обычный":
                cc[c]["reg"] += 1
            else:
                cc[c]["aged"] += 1
        for c, s in cc.items():
            flag = s.get("flag") or ""
            text += f"{flag} {c}: {s['reg']} обычных, {s['aged']} с отлегой\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn("Назад", emoji_key="back", callback_data="admin_panel")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, text, reply_markup=kb)
    await call.answer()

# ---- Broadcast ----
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "Введите текст для рассылки:")
    await state.set_state(Broadcast.waiting_text)
    await call.answer()

@router.message(Broadcast.waiting_text)
async def broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    users = await db_all("SELECT user_id FROM users")
    ok, fail = 0, 0
    for u in users:
        try:
            await message.copy_to(u["user_id"])
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await message.answer(f"{e('auto_check','✅')} Рассылка завершена!\nУспешно: {ok}\nНеудачно: {fail}")
    await state.clear()

# ---- Admin topup ----
@router.callback_query(F.data == "admin_topup_user")
async def admin_topup_user(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "Введите ID и сумму:\n<code>123456789 100</code>")
    await state.set_state(AdminTopup.waiting_input)
    await call.answer()

@router.message(AdminTopup.waiting_input)
async def process_topup(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    p = message.text.split()
    if len(p) != 2:
        await message.answer(f"{e('error','❌')} Неверный формат!")
        return
    try:
        uid = int(p[0])
        amt = float(p[1])
    except Exception:
        await message.answer(f"{e('error','❌')} Неверный формат!")
        return
    u = await get_user(uid)
    if not u:
        await message.answer(f"{e('error','❌')} Не найден!")
        await state.clear()
        return
    await update_balance(uid, u["balance"] + amt)
    await db_exec("INSERT INTO topup_history (user_id, amount, method, created_at) VALUES (?,?,?,?)",
                  (uid, amt, "Админ", datetime.now().isoformat()))
    await message.answer(f"{e('auto_check','✅')} Баланс {uid} пополнен на {format_price(amt)}")
    await state.clear()

# ---- Referrals ----
@router.callback_query(F.data == "admin_referrals")
async def admin_referrals(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    refs = await db_all("SELECT * FROM referrals")
    if not refs:
        await call.answer("Нет рефералов", show_alert=True)
        return
    st = {}
    for r in refs:
        uid = r["user_id"]
        if uid not in st:
            st[uid] = {"total": 0, "purchased": 0}
        st[uid]["total"] += 1
        if r.get("has_purchased"):
            st[uid]["purchased"] += 1
    text = "<b>Статистика рефералов:</b>\n\n"
    for uid, s in sorted(st.items(), key=lambda x: x[1]["total"], reverse=True):
        u = await get_user(uid)
        un = u["username"] if u else "Неизвестный"
        text += f"@{un} (ID: {uid})\nПригласил: {s['total']} | Купили: {s['purchased']}\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn("Назад", emoji_key="back", callback_data="admin_panel")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, text, reply_markup=kb)
    await call.answer()

# ---- Ban ----
@router.callback_query(F.data == "admin_ban")
async def admin_ban_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "Введите ID или @username для бана:")
    await state.set_state(BanUser.waiting_ban_id)
    await call.answer()

@router.message(BanUser.waiting_ban_id)
async def admin_ban_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    t = message.text.strip()
    u = None
    if t.startswith("@"):
        u = await db_one("SELECT * FROM users WHERE username = ?", (t[1:],))
    else:
        try:
            u = await get_user(int(t))
        except Exception:
            pass
    if not u:
        await message.answer(f"{e('error','❌')} Пользователь не найден в базе.")
        await state.clear()
        return
    uid = u["user_id"]
    if not await is_banned(uid):
        await db_exec("INSERT OR IGNORE INTO banned (user_id, banned_at) VALUES (?,?)", (uid, datetime.now().isoformat()))
        await message.answer(f"{e('banned','🚫')} Пользователь {uid} забанен.")
        try:
            await bot.send_message(uid, f"{e('banned','🚫')} Ваш тикет закрыт.")
        except Exception:
            pass
    else:
        await db_exec("DELETE FROM banned WHERE user_id = ?", (uid,))
        await message.answer(f"{e('auto_check','✅')} Пользователь {uid} разбанен.")
    await state.clear()

# ---- Promo ----
@router.callback_query(F.data == "admin_promo")
async def admin_promo_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, "<b>Создание промокода</b>\n\nВведите данные в формате:\n<code>КОД СУММА АКТИВАЦИИ</code>\n\nПример: <code>START50 50 10</code>")
    await state.set_state(AdminPromo.waiting_input)
    await call.answer()

@router.message(AdminPromo.waiting_input)
async def process_promo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    p = message.text.split()
    if len(p) != 3:
        await message.answer(f"{e('error','❌')} Неверный формат!")
        return
    try:
        code = p[0].upper()
        amt = float(p[1])
        act = int(p[2])
    except Exception:
        await message.answer(f"{e('error','❌')} Неверный формат!")
        return
    if await db_one("SELECT 1 FROM promocodes WHERE code = ?", (code,)):
        await message.answer(f"{e('error','❌')} Промокод с таким названием уже существует.")
        await state.clear()
        return
    await db_exec("INSERT INTO promocodes (code, amount, activations, created_at) VALUES (?,?,?,?)",
                  (code, amt, act, datetime.now().isoformat()))
    await message.answer(f"{e('auto_check','✅')} Промокод <b>{code}</b> создан!\nСумма: {format_price(amt)}\nАктиваций: {act}")
    await state.clear()

# ---- Users ----
@router.callback_query(F.data == "admin_users")
async def admin_users_start(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    total = await tcount("users")
    rows = await db_all("SELECT user_id, username FROM users LIMIT 50")
    kb_rows, buf = [], []
    for u in rows:
        buf.append(InlineKeyboardButton(text=f"@{u.get('username','Неизвестный')}", callback_data=f"user_info_{u['user_id']}"))
        if len(buf) == 2:
            kb_rows.append(buf)
            buf = []
    if buf:
        kb_rows.append(buf)
    kb_rows.append([btn("Назад", emoji_key="back", callback_data="admin_panel")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, f"<b>Всего пользователей: {total}</b>\n\nВыберите пользователя:", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("user_info_"))
async def admin_user_info(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    uid = int(call.data.replace("user_info_", ""))
    u = await get_user(uid)
    if not u:
        await call.answer("Не найден!", show_alert=True)
        return
    tups = await db_all("SELECT * FROM topup_history WHERE user_id = ?", (uid,))
    purs = await db_all("SELECT * FROM purchase_history WHERE user_id = ?", (uid,))
    total = sum(t.get("amount", 0) for t in tups)
    text = (
        f"<b>@{u.get('username','Неизвестный')}</b>\n\n"
        f"ID: <code>{uid}</code>\n"
        f"{e('balance','💰')} Баланс: {format_price(u.get('balance', 0))}\n"
        f"Всего пополнено: {format_price(total)}\n"
        f"Пополнений: {len(tups)}\n"
        f"Покупок: {len(purs)}\n\n"
    )
    if purs:
        text += "<b>История покупок:</b>\n"
        for p in purs[-10:]:
            text += f"• <code>{p.get('phone')}</code> ({p.get('country')}) — {format_price(p.get('price', 0))}\n"
        text += "\n"
    if tups:
        text += "<b>История пополнений:</b>\n"
        for t in tups[-10:]:
            text += f"• {format_price(t.get('amount', 0))} — {t.get('method', '?')}\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn("Назад", emoji_key="back", callback_data="admin_users")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, text, reply_markup=kb)
    await call.answer()

# ---- Giveaway ----
@router.callback_query(F.data == "admin_giveaway")
async def admin_giveaway_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await bot.send_message(call.from_user.id, f"{e('prize','🎁')} <b>Создание розыгрыша</b>\n\nОтправьте приз — любой текст, который увидят участники.\nНапример: <code>Аккаунт США 2024 года</code>")
    await state.set_state(Giveaway.waiting_prize)
    await call.answer()

@router.message(Giveaway.waiting_prize)
async def giveaway_set_prize(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    await state.update_data(prize=message.text)
    await message.answer("Теперь укажите <b>количество участников</b> — целое число.\nНапример: <code>15</code>")
    await state.set_state(Giveaway.waiting_participants)

@router.message(Giveaway.waiting_participants)
async def giveaway_set_participants(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        total = int(message.text.strip())
        if total < 2 or total > 1000:
            await message.answer(f"{e('error','❌')} Введите число от 2 до 1000.")
            return
    except Exception:
        await message.answer(f"{e('error','❌')} Введите целое число.")
        return
    d = await state.get_data()
    prize = d.get("prize")
    gid = await db_exec("INSERT INTO giveaways (prize, total, participants, message_ids, status, created_by, created_at) VALUES (?,?,?,?,?,?,?)",
                        (prize, total, "[]", "{}", "active", message.from_user.id, datetime.now().isoformat()))
    await message.answer(f"{e('auto_check','✅')} <b>Розыгрыш создан!</b>\n\n{e('prize','🎁')} Приз: {prize}\nУчастников: {total}\n\nРассылка запущена.")
    users = await db_all("SELECT user_id FROM users")
    sent = 0
    mids = {}
    for u in users:
        uid = u.get("user_id")
        if not uid:
            continue
        try:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [btn(f"Участвовать (0/{total})", emoji_key="join", style="danger", callback_data=f"giveaway_join_{gid}")]
            ])
            text = (
                f"{e('prize','🎁')} <b>Розыгрыш!</b>\n\n"
                f"Приз: <b>{prize}</b>\n"
                f"Участников: <b>0/{total}</b>\n\n"
                f"{e('warning','⚠️')} Участвовать могут только те, у кого было пополнение баланса "
                f"от 100 ₽ за последние 21 день.\n\n"
                f"Жми кнопку ниже, чтобы участвовать"
            )
            m = await bot.send_message(uid, text, reply_markup=kb)
            mids[str(uid)] = m.message_id
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await db_exec("UPDATE giveaways SET message_ids = ? WHERE doc_id = ?", (json.dumps(mids, ensure_ascii=False), gid))
    await message.answer(f"Рассылка завершена. Отправлено: {sent}")
    await state.clear()

@router.callback_query(F.data.startswith("giveaway_join_"))
async def giveaway_join(call: CallbackQuery):
    try:
        gid = int(call.data.replace("giveaway_join_", ""))
    except Exception:
        await call.answer("Ошибка!", show_alert=True)
        return
    g = await db_one("SELECT * FROM giveaways WHERE doc_id = ?", (gid,))
    if not g:
        await call.answer("Розыгрыш не найден.", show_alert=True)
        return
    if g.get("status") != "active":
        await call.answer("Розыгрыш уже завершён.", show_alert=True)
        return
    parts = json.loads(g.get("participants") or "[]")
    total = g.get("total", 0)
    uid = call.from_user.id
    if uid in parts:
        await call.answer("Вы уже участвуете.", show_alert=True)
        return
    if len(parts) >= total:
        await call.answer("Мест больше нет.", show_alert=True)
        return
    if not await has_deposit_last_21_days(uid, 100):
        await call.answer("Участвовать могут только те, у кого сумма пополнений за последние 21 день составляет от 100 ₽.", show_alert=True)
        return
    parts.append(uid)
    await db_exec("UPDATE giveaways SET participants = ? WHERE doc_id = ?", (json.dumps(parts), gid))
    nn = len(parts)
    pr = g.get("prize", "приз")
    newkb = InlineKeyboardMarkup(inline_keyboard=[
        [btn(f"Участвовать ({nn}/{total})", emoji_key="join", style="danger", callback_data=f"giveaway_join_{gid}")]
    ])
    text = (
        f"{e('prize','🎁')} <b>Розыгрыш!</b>\n\n"
        f"Приз: <b>{pr}</b>\n"
        f"Участников: <b>{nn}/{total}</b>\n\n"
        f"{e('warning','⚠️')} Участвовать могут только те, у кого было пополнение баланса "
        f"от 100 ₽ за последние 21 день."
    )
    try:
        await call.message.edit_reply_markup(reply_markup=newkb)
    except Exception:
        pass
    mids = json.loads(g.get("message_ids") or "{}")
    for pu in parts:
        mid = mids.get(str(pu))
        if not mid:
            continue
        try:
            await bot.edit_message_text(chat_id=pu, message_id=mid, text=text, reply_markup=newkb)
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await call.answer(f"Вы участвуете! ({nn}/{total})")
    if nn >= total:
        try:
            await run_giveaway(gid)
        except Exception as ex:
            logging.error(f"run_giveaway failed (join): {ex}")

async def run_giveaway(gid):
    try:
        g = await db_one("SELECT * FROM giveaways WHERE doc_id = ?", (gid,))
        if not g or g.get("status") == "finished":
            return
        parts = json.loads(g.get("participants") or "[]")
        pr = g.get("prize", "приз")
        if not parts:
            await db_exec("UPDATE giveaways SET status = 'finished' WHERE doc_id = ?", (gid,))
            return
        scores = {p: random.randint(0, 40) for p in parts}
        w = max(scores, key=scores.get)
        ws = scores[w]
        await db_exec("UPDATE giveaways SET status = 'finished', finished_at = ?, winner_id = ?, winner_score = ?, results = ? WHERE doc_id = ?",
                      (datetime.now().isoformat(), w, ws, json.dumps({str(k): v for k, v in scores.items()}), gid))
        try:
            await bot.send_message(w,
                f"{e('congrats','🏆')} <b>Поздравляем!</b>\n\n"
                f"Вы выиграли в розыгрыше!\n"
                f"{e('prize','🎁')} Приз: <b>{pr}</b>\n"
                f"{e('score','⭐')} Ваш результат: <b>{ws}</b> баллов\n\n"
                f"Напишите админу @{SUPPORT_USERNAME}, чтобы забрать приз."
            )
        except Exception:
            pass
        wu = await get_user(w)
        wn = f"@{wu['username']}" if wu and wu.get("username") and wu["username"] != "Неизвестный" else f'<a href="tg://user?id={w}">Победитель</a>'
        for pu in parts:
            if pu == w:
                continue
            try:
                await bot.send_message(pu,
                    f"{e('prize','🎁')} <b>Розыгрыш завершён.</b>\n\n"
                    f"Приз: <b>{pr}</b>\n"
                    f"{e('score','⭐')} Ваш результат: <b>{scores[pu]}</b> баллов\n"
                    f"Победил: {wn} (результат {ws})\n\n"
                    f"В следующий раз повезёт больше!"
                )
            except Exception:
                pass
            await asyncio.sleep(0.05)
    except Exception as ex:
        logging.error(f"run_giveaway error: {ex}")

# ==================== HTTP /topup ====================
web_app = web.Application()

async def handle_topup(request):
    try:
        d = await request.json()
        if d.get("secret") != API_SECRET:
            return web.json_response({"status": "error", "message": "Неверный ключ"})
        uid = int(d["user_id"])
        amt = float(d["amount"])
        u = await get_user(uid)
        if not u:
            return web.json_response({"status": "error", "message": "Юзер не найден"})
        await update_balance(uid, u["balance"] + amt)
        await db_exec("INSERT INTO topup_history (user_id, amount, method, created_at) VALUES (?,?,?,?)",
                      (uid, amt, "Stars", datetime.now().isoformat()))
        try:
            await bot.send_message(uid, f"{e('auto_check','✅')} Баланс пополнен на {format_price(amt)} через Stars!")
        except Exception:
            pass
        return web.json_response({"status": "ok", "new_balance": u["balance"] + amt})
    except Exception as ex:
        logging.error(f"Topup error: {ex}")
        return web.json_response({"status": "error", "message": str(ex)})

web_app.router.add_post("/topup", handle_topup)

# ==================== СТАРТ ====================
async def on_startup():
    logging.info("Запуск...")
    try:
        await bot.set_my_commands([BotCommand(command="start", description="Открыть главное меню")])
        logging.info("Команды бота зарегистрированы")
    except Exception as ex:
        logging.error(f"Ошибка регистрации команд: {ex}")
    try:
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        logging.info("Кнопка меню установлена")
    except Exception as ex:
        logging.error(f"Ошибка установки кнопки меню: {ex}")
    global TON_WALLET_RAW
    TON_WALLET_RAW = convert_address_to_raw(TON_WALLET)
    logging.info(f"TON_WALLET_RAW: {TON_WALLET_RAW}")
    await init_db()
    await migrate_from_json()
    await restore_userbots_from_db()
    if await start_main_userbot():
        logging.info("Юзербот авторизован")
    else:
        logging.info("Ожидание кода...")
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8080)
    await site.start()
    logging.info("HTTP сервер запущен на порту 8080")
    asyncio.create_task(check_accounts_health())
    asyncio.create_task(check_ton_transactions())
    asyncio.create_task(check_giveaways())

async def main():
    await on_startup()
    await asyncio.gather(
        dp.start_polling(bot),
        dp_second.start_polling(second_bot),
    )

if __name__ == "__main__":
    asyncio.run(main())