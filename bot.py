import os
import logging
from collections import defaultdict
from datetime import datetime

from openai import OpenAI
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# 🔥 CONFIGURATION
# =========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN manquant")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY manquant")

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================================================
# 📊 LOGGING PRO
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | LUST AI | %(levelname)s | %(message)s"
)

logger = logging.getLogger("LUST_AI")

# =========================================================
# 🧠 PERSONNALITÉS LUST AI
# =========================================================

PERSONNALITES = {
    "serieux": ("🎓 Sérieux", "Tu es un assistant précis et professionnel."),
    "decontracte": ("😎 Décontracté", "Tu es un ami cool et naturel."),
    "poete": ("🌹 Poète", "Réponses poétiques et imagées."),
    "humoriste": ("😂 Humoriste", "Humour intelligent dans chaque réponse."),
    "philosophe": ("🧠 Philosophe", "Réflexion profonde et philosophique."),
    "coach": ("💪 Coach", "Motivation, discipline et énergie."),
    "dark": ("🌑 Dark LUST", "Style mystérieux et intense."),
    "genius": ("🧬 Génie", "Explications ultra claires et intelligentes."),
}

# =========================================================
# 💾 MÉMOIRE UTILISATEUR
# =========================================================

user_style = defaultdict(lambda: "serieux")
user_history = defaultdict(list)
user_stats = defaultdict(lambda: {"messages": 0})

MAX_HISTORY = 10

# =========================================================
# 🧰 UTILITAIRES
# =========================================================

def build_menu():
    return [
        [InlineKeyboardButton(name, callback_data=f"style_{key}")]
        for key, (name, _) in PERSONNALITES.items()
    ]

def get_system_prompt(style_key: str) -> str:
    return PERSONNALITES.get(style_key, PERSONNALITES["serieux"])[1]

def add_history(uid, role, content):
    history = user_history[uid]
    history.append({"role": role, "content": content})
    user_history[uid] = history[-MAX_HISTORY:]

def safe_text(update: Update):
    return update.message.text if update.message and update.message.text else None

# =========================================================
# 🚀 COMMANDES
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *LUST AI BOT*\n\nChoisis ton style :",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(build_menu())
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 COMMANDES\n"
        "/start - démarrer\n"
        "/help - aide\n"
        "/style - changer style\n"
        "/reset - reset mémoire\n"
        "/ping - test bot\n"
        "/stats - stats",
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 LUST AI ONLINE")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_history[uid].clear()
    await update.message.reply_text("🧹 Mémoire reset")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    count = user_stats[uid]["messages"]
    await update.message.reply_text(f"📊 Messages: {count}")

async def style_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎭 Choisis ton style :",
        reply_markup=InlineKeyboardMarkup(build_menu())
    )

# =========================================================
# 🔘 CALLBACK BUTTONS
# =========================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    style_key = query.data.replace("style_", "")
    user_style[query.from_user.id] = style_key

    name, _ = PERSONNALITES.get(style_key, ("Sérieux", ""))

    await query.edit_message_text(f"✅ Style activé : {name}")

# =========================================================
# 🤖 IA CORE
# =========================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = safe_text(update)

    if not text:
        return

    user_stats[uid]["messages"] += 1
    style = user_style[uid]

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    try:
        messages = [
            {"role": "system", "content": get_system_prompt(style)},
            *user_history[uid],
            {"role": "user", "content": text},
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
        )

        answer = response.choices[0].message.content.strip()

        add_history(uid, "user", text)
        add_history(uid, "assistant", answer)

        await update.message.reply_text(
            f"{answer}\n\n— LUST AI ⚡"
        )

    except Exception as e:
        logger.exception("OpenAI/Telegram error")
        await update.message.reply_text(
            "❌ Erreur IA temporaire, réessaie."
        )

# =========================================================
# 🧠 STARTUP LOG
# =========================================================

async def post_init(app):
    logger.info("🔥 LUST AI BOT READY")

# =========================================================
# 🚀 MAIN APP
# =========================================================

def main():
    logger.info("🚀 Booting LUST AI BOT...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("style", style_cmd))

    # Buttons
    app.add_handler(CallbackQueryHandler(button_handler))

    # Messages
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("⚡ Bot running in polling mode")
    app.run_polling()

# =========================================================
# 🧨 ENTRYPOINT SAFE
# =========================================================

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("💥 FATAL CRASH LUST AI BOT")