import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters, ConversationHandler,
)

# ───────────────────── CONFIG ─────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8231310378:AAEfSkfK_djI2FP1KbBe2X4KZgoG8ivQwkU")

# ✅ Add your Telegram user ID here (get it from @userinfobot)
ADMIN_IDS = set(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else set()

DATA_FILE = "data.json"

# ConversationHandler states
BROADCAST_MSG    = 1
ADD_BROKER_NAME  = 2
ADD_BROKER_LINK  = 3
ADD_BROKER_DESC  = 4
ADD_BROKER_DEP   = 5
EDIT_BROKER_LINK = 6
ADD_VPS_NAME     = 7
ADD_VPS_LINK     = 8
REMOVE_ADMIN_ID  = 9
ADD_ADMIN_ID     = 10

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ───────────────────── DATA STORE ─────────────────────

DEFAULT_DATA = {
    "users": {},        # {user_id: {name, username, joined}}
    "admins": [],       # list of admin user IDs
    "brokers": {
        "exness": {
            "name": "Exness",
            "link": "https://one.exnessonelink.com/a/uhk6peieiq",
            "badge": "⭐ Most Popular",
            "desc": "Fast withdrawals • Low spread • Instant execution",
            "min_deposit": "$10",
            "rating": "9.8/10",
            "regulated": "FCA, CySEC, FSA",
            "active": True
        },
        "icmarkets": {
            "name": "IC Markets",
            "link": "https://icmarkets.com/?camp=78272",
            "badge": "🏆 Best ECN",
            "desc": "0.0 pips spread • Raw ECN pricing • Best for scalping",
            "min_deposit": "$200",
            "rating": "9.5/10",
            "regulated": "ASIC, CySEC, FSA",
            "active": True
        },
        "tickmill": {
            "name": "Tickmill",
            "link": "https://tickmill.link/3RimUpD",
            "badge": "⚡ Ultra Fast",
            "desc": "Ultra low latency • FCA regulated • Professional grade",
            "min_deposit": "$100",
            "rating": "9.2/10",
            "regulated": "FCA, CySEC, FSCA",
            "active": True
        },
        "vantage": {
            "name": "Vantage",
            "link": "https://vigco.co/la-com-inv/bbfxai",
            "badge": "🌍 Global Broker",
            "desc": "High leverage • MT4/MT5 • Wide instrument range",
            "min_deposit": "$50",
            "rating": "9.0/10",
            "regulated": "ASIC, FCA, CIMA",
            "active": True
        },
    },
    "vps": {
        "govpsfx": {
            "name": "GoVPS FX",
            "link": "https://my.govpsfx.com/?ref=NDM0ODU6OlJV",
            "active": True
        }
    },
    "telegram_link": "https://t.me/BBFx_Ai",
    "website": "https://xauusdrobot.com",
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        # merge missing keys from default
        for k, v in DEFAULT_DATA.items():
            if k not in data:
                data[k] = v
        return data
    return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_admin(user_id: int, data: dict) -> bool:
    return user_id in ADMIN_IDS or user_id in data.get("admins", [])

def register_user(user, data):
    uid = str(user.id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": user.full_name,
            "username": user.username or "",
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        save_data(data)

# ───────────────────── MESSAGES ─────────────────────

WELCOME_MSG = """
🤖 *Welcome to XAUUSD Robot!*

Hello *{name}*! 👋

I'm your personal guide to getting a *FREE Gold Trading EA* for MetaTrader 4 & 5.

Here's what I can help you with:
🥇 Get your *Free XAUUSD Expert Advisor*
🏦 Choose from *Trusted Brokers*
💻 Set up *VPS Hosting* for 24/7 trading
⚙️ Understand the full *Algo Trading Process*

✅ *2,500+ traders* already using our free EA!

👇 *What would you like to do?*
"""

HOW_MSG = """
⚙️ *How to Get Your Free EA — 3 Simple Steps*

━━━━━━━━━━━━━━━━━━━━

*STEP 1 — Open a Broker Account* 🏦
Register a live trading account with one of our recommended brokers using our affiliate link.
⏱ Takes only 5–10 minutes | Starts from just $10

*STEP 2 — Contact Us on Telegram* 💬
Send your account confirmation screenshot to *@BBFx\\_Ai* on Telegram.
Our team verifies your account within 24 hours.

*STEP 3 — Receive Your Free EA* 🎉
We install the XAUUSD Expert Advisor directly on your MT4/MT5 platform — completely free.
No subscriptions. No hidden fees. Yours for life!

━━━━━━━━━━━━━━━━━━━━
🤖 *What Does the EA Do Automatically?*
• Executes Gold (XAUUSD) trades 24 hours a day, 5 days a week
• Uses AI to identify high-probability entry points
• Pauses trading before major news events (built-in News Filter)
• Manages Stop Loss and Take Profit automatically
• Historical win rate: ~85%

⚠️ _Risk Disclaimer: Past performance does not guarantee future results. Trading involves risk of capital loss._
"""

ALGOS_MSG = """
🤖 *Free Trading Robots — All Completely FREE!*

━━━━━━━━━━━━━━━━━━━━
Open any broker account via our link and receive all of these bots free:

🥇 *XAUUSD Gold Robot*
Our flagship EA. AI-driven entry logic with built-in news filter for Gold (XAU/USD).

📈 *Gold Scalper Pro EA*
High-frequency scalping strategy designed for fast gold trades.

⚡ *MT5 Gold Algo*
Fully optimized for the MetaTrader 5 platform.

₿ *BTC Momentum Bot*
Momentum-based strategy for Bitcoin (BTC/USD).

💶 *EURUSD Trend EA*
Reliable trend-following algorithm for the EUR/USD pair.

━━━━━━━━━━━━━━━━━━━━
📋 *All Algos Include:*
• Compatible with MT4 & MT5
• No coding knowledge required
• Free installation support via Telegram
• Cost: *100% Free*
"""

FEATURES_MSG = """
🔥 *XAUUSD Robot — Full Feature List*

━━━━━━━━━━━━━━━━━━━━

🤖 *AI-Powered Entry Logic*
ML models scan M5, M15, H1, and H4 timeframes simultaneously to identify high-probability XAUUSD setups.

📰 *Smart News Filter*
Automatically pauses before NFP, FOMC, CPI and other high-impact events — protecting your positions from volatility spikes.

🛡️ *Multi-Layer Risk Management*
Hard stop-loss + trailing stop + max daily drawdown + fractional position sizing. Never martingale, never grid.

⚡ *ECN 12ms Execution*
Ultra-fast order execution. No slippage. No requotes.

❌ *No Martingale | No Grid*
Fixed fractional position sizing — risk per trade always proportional to your balance.

━━━━━━━━━━━━━━━━━━━━
📊 *Technical Specifications:*
• Platform: MT4 & MT5
• Asset: XAUUSD (Gold)
• Strategy: AI Scalping + Trend Following
• Execution: ECN 12ms
• Risk: Fixed Fractional
• News Filter: ✓ Built-in
• Martingale: ✗ Disabled
• Cost: 100% Free ✓
"""

HELP_MSG = """
📚 *Available Commands:*

/start — Main menu
/how — How to get your free EA (3 steps)
/brokers — View all brokers
/vps — VPS hosting information
/algos — Free trading robots list
/features — Full EA feature list
/help — This message

━━━━━━━━━━━━━━━━━━━━
🌐 Website: xauusdrobot.com
💬 Telegram Support: @BBFx_Ai
"""

# ───────────────────── KEYBOARDS ─────────────────────

def main_kb(data):
    tg = data.get("telegram_link", "https://t.me/BBFx_Ai")
    web = data.get("website", "https://xauusdrobot.com")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ How It Works", callback_data="how"),
         InlineKeyboardButton("🤖 Free Algos", callback_data="algos")],
        [InlineKeyboardButton("🏦 Choose Broker", callback_data="brokers")],
        [InlineKeyboardButton("💻 VPS Hosting", callback_data="vps"),
         InlineKeyboardButton("🔥 EA Features", callback_data="features")],
        [InlineKeyboardButton("📞 Telegram Support", url=tg),
         InlineKeyboardButton("🌐 Website", url=web)],
    ])

def brokers_kb(data):
    rows = []
    flags = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣"]
    active = [(k, v) for k, v in data["brokers"].items() if v.get("active", True)]
    for i, (key, b) in enumerate(active):
        flag = flags[i] if i < len(flags) else "🔹"
        rows.append([InlineKeyboardButton(
            f"{flag} {b['name']}  {b.get('badge','')}  |  Min {b.get('min_deposit','—')}",
            callback_data=f"broker_{key}"
        )])
    rows.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main")])
    return InlineKeyboardMarkup(rows)

def broker_detail_kb(key, link, tg):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Open Account →", url=link)],
        [InlineKeyboardButton("💬 Message Us After Opening →", url=tg)],
        [InlineKeyboardButton("⬅️ Other Brokers", callback_data="brokers"),
         InlineKeyboardButton("🏠 Home", callback_data="main")],
    ])

def vps_kb(data):
    rows = []
    active_vps = [(k, v) for k, v in data.get("vps", {}).items() if v.get("active", True)]
    for key, v in active_vps:
        rows.append([InlineKeyboardButton(f"🚀 {v['name']} — Get VPS →", url=v["link"])])
    rows.append([InlineKeyboardButton("🏦 Select a Broker", callback_data="brokers"),
                 InlineKeyboardButton("🏠 Home", callback_data="main")])
    return InlineKeyboardMarkup(rows)

def back_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏦 Choose a Broker", callback_data="brokers"),
         InlineKeyboardButton("💻 VPS Info", callback_data="vps")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main")],
    ])

# ───────── ADMIN KEYBOARDS ─────────

def admin_main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast")],
        [InlineKeyboardButton("🏦 Manage Brokers", callback_data="adm_brokers"),
         InlineKeyboardButton("💻 Manage VPS", callback_data="adm_vps")],
        [InlineKeyboardButton("👥 Manage Admins", callback_data="adm_admins"),
         InlineKeyboardButton("📊 Bot Stats", callback_data="adm_stats")],
        [InlineKeyboardButton("❌ Close", callback_data="adm_close")],
    ])

def admin_brokers_kb(data):
    rows = []
    for key, b in data["brokers"].items():
        status = "✅" if b.get("active", True) else "❌"
        rows.append([
            InlineKeyboardButton(f"{status} {b['name']}", callback_data=f"adm_broker_view_{key}"),
        ])
    rows.append([InlineKeyboardButton("➕ Add New Broker", callback_data="adm_broker_add")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)

def admin_broker_detail_kb(key, active):
    toggle_label = "❌ Disable" if active else "✅ Enable"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Edit Link", callback_data=f"adm_broker_editlink_{key}")],
        [InlineKeyboardButton(toggle_label, callback_data=f"adm_broker_toggle_{key}"),
         InlineKeyboardButton("🗑️ Delete", callback_data=f"adm_broker_delete_{key}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="adm_brokers")],
    ])

def admin_vps_kb(data):
    rows = []
    for key, v in data.get("vps", {}).items():
        status = "✅" if v.get("active", True) else "❌"
        rows.append([InlineKeyboardButton(f"{status} {v['name']}", callback_data=f"adm_vps_view_{key}")])
    rows.append([InlineKeyboardButton("➕ Add New VPS", callback_data="adm_vps_add")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)

def admin_vps_detail_kb(key, active):
    toggle_label = "❌ Disable" if active else "✅ Enable"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data=f"adm_vps_toggle_{key}"),
         InlineKeyboardButton("🗑️ Delete", callback_data=f"adm_vps_delete_{key}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="adm_vps")],
    ])

def admin_admins_kb(data):
    rows = []
    all_admins = list(ADMIN_IDS) + data.get("admins", [])
    for aid in set(all_admins):
        is_super = aid in ADMIN_IDS
        label = f"👑 {aid} (Super)" if is_super else f"👤 {aid}"
        rows.append([InlineKeyboardButton(label, callback_data=f"adm_admin_view_{aid}")])
    rows.append([InlineKeyboardButton("➕ Add Admin", callback_data="adm_admin_add")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)

# ───────────────────── USER COMMANDS ─────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = update.effective_user
    register_user(user, data)
    name = user.first_name or "Trader"
    await update.message.reply_text(
        WELCOME_MSG.format(name=name),
        parse_mode="Markdown", reply_markup=main_kb(data)
    )

async def cmd_how(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HOW_MSG, parse_mode="Markdown", reply_markup=back_kb())

async def cmd_brokers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(
        "🏦 *Choose Your Broker — All Give You a Free EA!*\n\nTap any broker below to see details 👇",
        parse_mode="Markdown", reply_markup=brokers_kb(data)
    )

async def cmd_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(
        "💻 *VPS Hosting — Run Your EA 24/7*\n\nA VPS keeps your EA running even when your PC is off.",
        parse_mode="Markdown", reply_markup=vps_kb(data)
    )

async def cmd_algos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ALGOS_MSG, parse_mode="Markdown", reply_markup=back_kb())

async def cmd_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(FEATURES_MSG, parse_mode="Markdown", reply_markup=back_kb())

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(HELP_MSG, parse_mode="Markdown", reply_markup=main_kb(data))

# ───────────────────── ADMIN COMMAND ─────────────────────

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = update.effective_user
    if not is_admin(user.id, data):
        await update.message.reply_text("⛔ You don't have admin access.")
        return
    total_users = len(data["users"])
    await update.message.reply_text(
        f"🛠️ *Admin Panel*\n\n👥 Total Users: *{total_users}*\n\nWhat would you like to do?",
        parse_mode="Markdown", reply_markup=admin_main_kb()
    )

# ───────────────────── CALLBACK HANDLER ─────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = query.data
    data = load_data()
    user = query.from_user

    # ── USER CALLBACKS ──
    if d == "main":
        await query.edit_message_text(
            WELCOME_MSG.format(name=user.first_name or "Trader"),
            parse_mode="Markdown", reply_markup=main_kb(data)
        )
    elif d == "how":
        await query.edit_message_text(HOW_MSG, parse_mode="Markdown", reply_markup=back_kb())
    elif d == "brokers":
        await query.edit_message_text(
            "🏦 *Choose Your Broker — All Give You a Free EA!*\n\nTap any broker below to see details 👇",
            parse_mode="Markdown", reply_markup=brokers_kb(data)
        )
    elif d == "vps":
        await query.edit_message_text(
            "💻 *VPS Hosting — Run Your EA 24/7*\n\nA VPS keeps your EA running even when your PC is off.",
            parse_mode="Markdown", reply_markup=vps_kb(data)
        )
    elif d == "algos":
        await query.edit_message_text(ALGOS_MSG, parse_mode="Markdown", reply_markup=back_kb())
    elif d == "features":
        await query.edit_message_text(FEATURES_MSG, parse_mode="Markdown", reply_markup=back_kb())

    elif d.startswith("broker_") and not d.startswith("broker_adm"):
        key = d.replace("broker_", "")
        b = data["brokers"].get(key)
        if not b:
            await query.edit_message_text("❌ Broker not found.", reply_markup=brokers_kb(data))
            return
        tg = data.get("telegram_link", "https://t.me/BBFx_Ai")
        msg = f"""
🏦 *{b['name']} — {b.get('badge','')}*

━━━━━━━━━━━━━━━━━━━━
📋 *Overview:*
{b.get('desc','')}

💰 *Minimum Deposit:* {b.get('min_deposit','—')}
⭐ *Our Rating:* {b.get('rating','—')}
🏛️ *Regulated by:* {b.get('regulated','—')}
🎁 *Reward:* Free XAUUSD EA after account opening

━━━━━━━━━━━━━━━━━━━━
✅ *Step-by-Step:*
1️⃣ Click the button below to open your account
2️⃣ Complete KYC (upload your ID documents)
3️⃣ Take a screenshot of your confirmed account
4️⃣ Send the screenshot to *@BBFx\\_Ai* on Telegram
5️⃣ Receive your FREE EA within 24 hours ✅

⚠️ *Important:* You must use our affiliate link to qualify for the free EA.
"""
        await query.edit_message_text(
            msg, parse_mode="Markdown",
            reply_markup=broker_detail_kb(key, b["link"], tg)
        )

    # ── ADMIN CALLBACKS ──
    elif d.startswith("adm_"):
        if not is_admin(user.id, data):
            await query.answer("⛔ No admin access.", show_alert=True)
            return
        await handle_admin_callback(query, d, data, context)

async def handle_admin_callback(query, d, data, context):
    user = query.from_user

    if d == "adm_main":
        total = len(data["users"])
        await query.edit_message_text(
            f"🛠️ *Admin Panel*\n\n👥 Total Users: *{total}*\n\nWhat would you like to do?",
            parse_mode="Markdown", reply_markup=admin_main_kb()
        )

    elif d == "adm_stats":
        total = len(data["users"])
        brokers_count = len([b for b in data["brokers"].values() if b.get("active", True)])
        admins_count = len(set(list(ADMIN_IDS) + data.get("admins", [])))
        msg = f"""
📊 *Bot Statistics*

👥 Total Users: *{total}*
🏦 Active Brokers: *{brokers_count}*
👑 Admins: *{admins_count}*
"""
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="adm_main")]
        ]))

    elif d == "adm_broadcast":
        context.user_data["adm_action"] = "broadcast"
        await query.edit_message_text(
            "📢 *Broadcast Message*\n\nType your message below. It will be sent to all users.\n\nSend /cancel to cancel.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="adm_main")]])
        )

    elif d == "adm_brokers":
        await query.edit_message_text(
            "🏦 *Manage Brokers*\n\nTap a broker to edit, enable/disable, or delete it.",
            parse_mode="Markdown", reply_markup=admin_brokers_kb(data)
        )

    elif d.startswith("adm_broker_view_"):
        key = d.replace("adm_broker_view_", "")
        b = data["brokers"].get(key, {})
        status = "✅ Active" if b.get("active", True) else "❌ Disabled"
        msg = f"🏦 *{b.get('name','?')}*\n\nStatus: {status}\nLink: `{b.get('link','—')}`\nMin Deposit: {b.get('min_deposit','—')}"
        await query.edit_message_text(msg, parse_mode="Markdown",
            reply_markup=admin_broker_detail_kb(key, b.get("active", True)))

    elif d.startswith("adm_broker_toggle_"):
        key = d.replace("adm_broker_toggle_", "")
        if key in data["brokers"]:
            data["brokers"][key]["active"] = not data["brokers"][key].get("active", True)
            save_data(data)
            status = "enabled ✅" if data["brokers"][key]["active"] else "disabled ❌"
            await query.answer(f"{data['brokers'][key]['name']} {status}", show_alert=True)
            await query.edit_message_text(
                "🏦 *Manage Brokers*", parse_mode="Markdown",
                reply_markup=admin_brokers_kb(data)
            )

    elif d.startswith("adm_broker_delete_"):
        key = d.replace("adm_broker_delete_", "")
        name = data["brokers"].get(key, {}).get("name", key)
        del data["brokers"][key]
        save_data(data)
        await query.answer(f"🗑️ {name} deleted!", show_alert=True)
        await query.edit_message_text(
            "🏦 *Manage Brokers*", parse_mode="Markdown",
            reply_markup=admin_brokers_kb(data)
        )

    elif d.startswith("adm_broker_editlink_"):
        key = d.replace("adm_broker_editlink_", "")
        context.user_data["adm_action"] = f"edit_broker_link:{key}"
        await query.edit_message_text(
            f"✏️ *Edit Link for {data['brokers'][key]['name']}*\n\nSend the new affiliate link now.\n\nSend /cancel to cancel.",
            parse_mode="Markdown"
        )

    elif d == "adm_broker_add":
        context.user_data["adm_action"] = "add_broker_name"
        context.user_data["new_broker"] = {}
        await query.edit_message_text(
            "➕ *Add New Broker*\n\nStep 1/4 — Send the broker *name* (e.g. Pepperstone)\n\nSend /cancel to cancel.",
            parse_mode="Markdown"
        )

    elif d == "adm_vps":
        await query.edit_message_text(
            "💻 *Manage VPS*\n\nTap a VPS to edit or disable it.",
            parse_mode="Markdown", reply_markup=admin_vps_kb(data)
        )

    elif d.startswith("adm_vps_view_"):
        key = d.replace("adm_vps_view_", "")
        v = data["vps"].get(key, {})
        status = "✅ Active" if v.get("active", True) else "❌ Disabled"
        msg = f"💻 *{v.get('name','?')}*\n\nStatus: {status}\nLink: `{v.get('link','—')}`"
        await query.edit_message_text(msg, parse_mode="Markdown",
            reply_markup=admin_vps_detail_kb(key, v.get("active", True)))

    elif d.startswith("adm_vps_toggle_"):
        key = d.replace("adm_vps_toggle_", "")
        if key in data["vps"]:
            data["vps"][key]["active"] = not data["vps"][key].get("active", True)
            save_data(data)
            status = "enabled ✅" if data["vps"][key]["active"] else "disabled ❌"
            await query.answer(f"{data['vps'][key]['name']} {status}", show_alert=True)
            await query.edit_message_text("💻 *Manage VPS*", parse_mode="Markdown", reply_markup=admin_vps_kb(data))

    elif d.startswith("adm_vps_delete_"):
        key = d.replace("adm_vps_delete_", "")
        name = data["vps"].get(key, {}).get("name", key)
        del data["vps"][key]
        save_data(data)
        await query.answer(f"🗑️ {name} deleted!", show_alert=True)
        await query.edit_message_text("💻 *Manage VPS*", parse_mode="Markdown", reply_markup=admin_vps_kb(data))

    elif d == "adm_vps_add":
        context.user_data["adm_action"] = "add_vps_name"
        context.user_data["new_vps"] = {}
        await query.edit_message_text(
            "➕ *Add New VPS*\n\nStep 1/2 — Send the VPS *name*\n\nSend /cancel to cancel.",
            parse_mode="Markdown"
        )

    elif d == "adm_admins":
        await query.edit_message_text(
            "👥 *Manage Admins*", parse_mode="Markdown",
            reply_markup=admin_admins_kb(data)
        )

    elif d.startswith("adm_admin_view_"):
        aid = int(d.replace("adm_admin_view_", ""))
        is_super = aid in ADMIN_IDS
        label = "👑 Super Admin (hardcoded)" if is_super else "👤 Admin"
        kb = InlineKeyboardMarkup([
            [] if is_super else [InlineKeyboardButton("🗑️ Remove Admin", callback_data=f"adm_admin_remove_{aid}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="adm_admins")]
        ])
        await query.edit_message_text(
            f"👤 *Admin: {aid}*\n\nType: {label}",
            parse_mode="Markdown", reply_markup=kb
        )

    elif d.startswith("adm_admin_remove_"):
        aid = int(d.replace("adm_admin_remove_", ""))
        if aid in data.get("admins", []):
            data["admins"].remove(aid)
            save_data(data)
            await query.answer(f"✅ Admin {aid} removed!", show_alert=True)
        await query.edit_message_text(
            "👥 *Manage Admins*", parse_mode="Markdown",
            reply_markup=admin_admins_kb(data)
        )

    elif d == "adm_admin_add":
        context.user_data["adm_action"] = "add_admin_id"
        await query.edit_message_text(
            "➕ *Add New Admin*\n\nSend the Telegram *User ID* of the new admin.\n(They can get their ID from @userinfobot)\n\nSend /cancel to cancel.",
            parse_mode="Markdown"
        )

    elif d == "adm_close":
        await query.delete_message()

# ───────────────────── TEXT HANDLER (admin actions + fallback) ─────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = update.effective_user
    text = update.message.text.strip()

    if text == "/cancel":
        context.user_data.pop("adm_action", None)
        context.user_data.pop("new_broker", None)
        context.user_data.pop("new_vps", None)
        await update.message.reply_text("❌ Action cancelled.", reply_markup=main_kb(data))
        return

    action = context.user_data.get("adm_action")

    if action and is_admin(user.id, data):
        # ── BROADCAST ──
        if action == "broadcast":
            context.user_data.pop("adm_action", None)
            users = data["users"]
            sent = 0
            failed = 0
            await update.message.reply_text(f"📢 Sending to {len(users)} users...")
            for uid in users:
                try:
                    await context.bot.send_message(
                        chat_id=int(uid), text=text, parse_mode="Markdown"
                    )
                    sent += 1
                except Exception:
                    failed += 1
            await update.message.reply_text(
                f"✅ Broadcast complete!\n\n✉️ Sent: {sent}\n❌ Failed: {failed}",
                reply_markup=admin_main_kb()
            )

        # ── EDIT BROKER LINK ──
        elif action.startswith("edit_broker_link:"):
            key = action.split(":")[1]
            context.user_data.pop("adm_action", None)
            data["brokers"][key]["link"] = text
            save_data(data)
            await update.message.reply_text(
                f"✅ Link updated for *{data['brokers'][key]['name']}*!\n\nNew link: `{text}`",
                parse_mode="Markdown", reply_markup=admin_main_kb()
            )

        # ── ADD BROKER (multi-step) ──
        elif action == "add_broker_name":
            context.user_data["new_broker"]["name"] = text
            context.user_data["adm_action"] = "add_broker_link"
            await update.message.reply_text(
                f"Step 2/4 — Send the *affiliate link* for {text}:\n\nSend /cancel to cancel.",
                parse_mode="Markdown"
            )
        elif action == "add_broker_link":
            context.user_data["new_broker"]["link"] = text
            context.user_data["adm_action"] = "add_broker_desc"
            await update.message.reply_text(
                "Step 3/4 — Send a short *description* (e.g. Low spread • Fast withdrawal):\n\nSend /cancel to cancel.",
                parse_mode="Markdown"
            )
        elif action == "add_broker_desc":
            context.user_data["new_broker"]["desc"] = text
            context.user_data["adm_action"] = "add_broker_dep"
            await update.message.reply_text(
                "Step 4/4 — Send the *minimum deposit* (e.g. $50):\n\nSend /cancel to cancel.",
                parse_mode="Markdown"
            )
        elif action == "add_broker_dep":
            nb = context.user_data.pop("new_broker", {})
            context.user_data.pop("adm_action", None)
            nb["min_deposit"] = text
            nb["badge"] = "🆕 New"
            nb["rating"] = "—"
            nb["regulated"] = "—"
            nb["active"] = True
            key = nb["name"].lower().replace(" ", "_")
            data["brokers"][key] = nb
            save_data(data)
            await update.message.reply_text(
                f"✅ *{nb['name']}* added successfully!",
                parse_mode="Markdown", reply_markup=admin_main_kb()
            )

        # ── ADD VPS (multi-step) ──
        elif action == "add_vps_name":
            context.user_data["new_vps"]["name"] = text
            context.user_data["adm_action"] = "add_vps_link"
            await update.message.reply_text(
                f"Step 2/2 — Send the *affiliate link* for {text}:\n\nSend /cancel to cancel.",
                parse_mode="Markdown"
            )
        elif action == "add_vps_link":
            nv = context.user_data.pop("new_vps", {})
            context.user_data.pop("adm_action", None)
            nv["link"] = text
            nv["active"] = True
            key = nv["name"].lower().replace(" ", "_")
            if "vps" not in data:
                data["vps"] = {}
            data["vps"][key] = nv
            save_data(data)
            await update.message.reply_text(
                f"✅ VPS *{nv['name']}* added!",
                parse_mode="Markdown", reply_markup=admin_main_kb()
            )

        # ── ADD ADMIN ──
        elif action == "add_admin_id":
            context.user_data.pop("adm_action", None)
            try:
                new_id = int(text)
                if "admins" not in data:
                    data["admins"] = []
                if new_id not in data["admins"]:
                    data["admins"].append(new_id)
                    save_data(data)
                await update.message.reply_text(
                    f"✅ Admin *{new_id}* added successfully!",
                    parse_mode="Markdown", reply_markup=admin_main_kb()
                )
            except ValueError:
                await update.message.reply_text("❌ Invalid ID. Please send a numeric Telegram User ID.")
        return

    # ── DEFAULT FALLBACK ──
    await update.message.reply_text(
        "I didn't understand that. Use /help to see all commands or tap the menu below 👇",
        reply_markup=main_kb(data)
    )

# ───────────────────── MAIN ─────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("how",      cmd_how))
    app.add_handler(CommandHandler("brokers",  cmd_brokers))
    app.add_handler(CommandHandler("vps",      cmd_vps))
    app.add_handler(CommandHandler("algos",    cmd_algos))
    app.add_handler(CommandHandler("features", cmd_features))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("admin",    cmd_admin))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("✅ XAUUSD Robot Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
