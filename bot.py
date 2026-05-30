import logging
import os
from collections import defaultdict

from openai import OpenAI
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ==========================
# CONFIGURATION
# ==========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ==========================
# PERSONNALITÉS
# ==========================

PERSONNALITES = {
    "serieux": {
        "nom": "🎓 Assistant Sérieux",
        "description": "Professionnel et factuel",
        "prompt_systeme": "Tu es un assistant professionnel et précis."
    },

    "decontracte": {
        "nom": "😎 Ami Décontracté",
        "description": "Amical et cool",
        "prompt_systeme": "Tu es un ami sympathique. Tutoiement obligatoire."
    },

    "poete": {
        "nom": "🌹 Poète",
        "description": "Réponses poétiques",
        "prompt_systeme": "Réponds toujours sous forme poétique."
    },

    "humoriste": {
        "nom": "😂 Humoriste",
        "description": "Blagues et humour",
        "prompt_systeme": "Ajoute une touche d'humour à chaque réponse."
    },

    "philosophe": {
        "nom": "🧠 Philosophe",
        "description": "Réflexions profondes",
        "prompt_systeme": "Réponds comme un philosophe."
    },

    "coach": {
        "nom": "💪 Coach Motivant",
        "description": "Motivation et énergie",
        "prompt_systeme": "Réponds comme un coach motivant."
    }
}

# ==========================
# MÉMOIRES
# ==========================

user_styles = defaultdict(lambda: "serieux")
user_histories = defaultdict(list)

MAX_HISTORY = 10

# ==========================
# COMMANDES
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                perso["nom"],
                callback_data=f"style_{key}"
            )
        ]
        for key, perso in PERSONNALITES.items()
    ]

    await update.message.reply_text(
        "👋 Bienvenue sur le Bot IA Multi-Personnalités.\n\n"
        "Choisis un style :",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    user_histories[user_id] = []

    await update.message.reply_text(
        "🗑 Historique supprimé."
    )

# ==========================
# BOUTONS
# ==========================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    style_key = query.data.replace(
        "style_",
        ""
    )

    user_styles[query.from_user.id] = style_key

    await query.edit_message_text(
        f"✅ Style sélectionné : "
        f"{PERSONNALITES[style_key]['nom']}"
    )

# ==========================
# IA
# ==========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id
    user_text = update.message.text

    style = user_styles[user_id]

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:

        history = user_histories[user_id]

        messages = [
            {
                "role": "system",
                "content": PERSONNALITES[style]["prompt_systeme"]
            }
        ]

        messages.extend(history)

        messages.append(
            {
                "role": "user",
                "content": user_text
            }
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8
        )

        answer = response.choices[0].message.content

        history.append(
            {
                "role": "user",
                "content": user_text
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        user_histories[user_id] = history[-MAX_HISTORY:]

        await update.message.reply_text(answer)

    except Exception as e:

        logger.error(str(e))

        await update.message.reply_text(
            "❌ Erreur lors de la génération de la réponse."
        )

# ==========================
# MAIN
# ==========================

def main():

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("style", style)
    )

    application.add_handler(
        CommandHandler("reset", reset)
    )

    application.add_handler(
        CallbackQueryHandler(button_callback)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("✅ Bot démarré")

    application.run_polling()

if __name__ == "__main__":
    main()            model="gpt-4.1-mini", # Ou un autre modèle OpenAI compatible
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7, # Peut être ajusté pour plus ou moins de créativité
            max_tokens=500
        )
        ai_response = response.choices[0].message.content
        await update.message.reply_text(ai_response)
    except openai.APIError as e:
        logger.error(f"Erreur OpenAI: {e}")
        await update.message.reply_text(
            "Désolé, une erreur est survenue lors de la génération de la réponse de l'IA. Veuillez réessayer plus tard."
        )
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        await update.message.reply_text(
            "Désolé, une erreur inattendue est survenue. Veuillez réessayer plus tard."
        )

def main() -> None:
    """Démarre le bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Gestionnaires de commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("style", style_command))
    application.add_handler(CommandHandler("character", style_command)) # Alias pour /style

    # Gestionnaire de callbacks pour les boutons inline
    application.add_handler(CallbackQueryHandler(button))

    # Gestionnaire de messages textuels (réponses de l'IA)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_response))

    # Démarrer le bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
