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
    filters
)

# ==========================
# CONFIGURATION
# ==========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY manquante")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN manquante")

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | LUST AI | %(levelname)s | %(message)s"
)

logger = logging.getLogger("LUST_AI")

# ==========================
# PERSONNALITÉS LUST AI
# ==========================

PERSONNALITES = {
    "serieux": {
        "nom": "🎓 Sérieux",
        "prompt": "Tu es un assistant précis, professionnel et factuel."
    },
    "decontracte": {
        "nom": "😎 Décontracté",
        "prompt": "Tu es un ami cool, parle simplement et naturellement."
    },
    "poete": {
        "nom": "🌹 Poète",
        "prompt": "Réponds toujours avec un style poétique."
    },
    "humoriste": {
        "nom": "😂 Humoriste",
        "prompt": "Ajoute de l'humour intelligent dans chaque réponse."
    },
    "philosophe": {
        "nom": "🧠 Philosophe",
        "prompt": "Réponds comme un philosophe profond."
    },
    "coach": {
        "nom": "💪 Coach",
        "prompt": "Motivation, énergie et discipline dans tes réponses."
    },
    "dark": {
        "nom": "🌑 Dark LUST",
        "prompt": "Style mystérieux, sombre et puissant."
    },
    "genius": {
        "nom": "🧬 Génie",
        "prompt": "Explique tout clairement avec intelligence maximale."
    }
}

# ==========================
# MÉMOIRE UTILISATEUR
# ==========================

user_style = defaultdict(lambda: "serieux")
user_history = defaultdict(list)
user_stats = defaultdict(lambda: {"messages": 0})

MAX_HISTORY = 12

# ==========================
# UTILITAIRES
# ==========================

def build_menu():
    return [
        [InlineKeyboardButton(v["nom"], callback_data=f"style_{k}")]
        for k, v in PERSONNALITES.items()
    ]

def add_to_history(user_id, role, content):
    history = user_history[user_id]
    history.append({"role": role, "content": content})
    user_history[user_id] = history[-MAX_HISTORY:]

def get_prompt(style_key):
    return PERSONNALITES[style_key]["prompt"]

# ==========================
# COMMANDES
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = build_menu()

    await update.message.reply_text(
        "🚀 *LUST AI BOT*\n\n"
        "Choisis une personnalité :",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *COMMANDES LUST AI*\n\n"
        "/start - démarrer\n"
        "/help - aide\n"
        "/style - changer style\n"
        "/reset - reset mémoire\n"
        "/ping - test bot\n"
        "/info - infos utilisateur\n"
        "/stats - statistiques",
        parse_mode="Markdown"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 LUST AI est en ligne")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_history[uid] = []
    await update.message.reply_text("🗑 Mémoire réinitialisée.")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    style = user_style[uid]
    await update.message.reply_text(
        f"👤 ID: {uid}\n"
        f"🎭 Style: {PERSONNALITES[style]['nom']}"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    count = user_stats[uid]["messages"]
    await update.message.reply_text(
        f"📊 Messages envoyés: {count}"
    )

async def style_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ==========================
# BOUTONS
# ==========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    style_key = query.data.replace("style_", "")
    user_style[query.from_user.id] = style_key

    await query.edit_message_text(
        f"✅ Style activé : {PERSONNALITES[style_key]['nom']}"
    )

# ==========================
# IA CORE
# ==========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    style = user_style[uid]

    user_stats[uid]["messages"] += 1

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    try:
        messages = [
            {"role": "system", "content": get_prompt(style)}
        ]

        messages.extend(user_history[uid])

        messages.append({"role": "user", "content": text})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8
        )

        answer = response.choices[0].message.content

        add_to_history(uid, "user", text)
        add_to_history(uid, "assistant", answer)

        await update.message.reply_text(
            answer + "\n\n— LUST AI ⚡"
        )

    except Exception as e:
        logger.exception("Erreur IA")
        await update.message.reply_text(
            "❌ Erreur IA. Réessaie plus tard."
        )

# ==========================
# APPLICATION
# ==========================

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("style", style_cmd))

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("🔥 LUST AI BOT démarré")
    app.run_polling()

# ==========================
# START
# ==========================

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Crash LUST AI BOT")