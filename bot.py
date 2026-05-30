
import logging
import os
from collections import defaultdict

import openai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

# Configuration de l'API OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Configuration du logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token du bot Telegram (à remplacer par le token fourni par l'utilisateur)
TELEGRAM_BOT_TOKEN = "8576498710:AAF9LeBEVTjet9QQjGr8976Mr2IzOLzbBus"

# Définition des personnages/styles de conversation
PERSONNALITES = {
    "serieux": {
        "nom": "Assistant Sérieux",
        "description": "Un assistant professionnel et factuel, répondant avec précision et clarté.",
        "prompt_systeme": "Vous êtes un assistant professionnel et factuel. Répondez avec précision, clarté et concision. Votre objectif est d'informer et d'aider l'utilisateur de manière sérieuse."
    },
    "decontracte": {
        "nom": "Ami Décontracté",
        "description": "Un ami amical et informel, utilisant un langage courant et un ton léger.",
        "prompt_systeme": "Vous êtes un ami décontracté et amical. Utilisez un langage informel, des expressions courantes et un ton léger. N'hésitez pas à faire des blagues ou des commentaires amusants."
    },
    "poete": {
        "nom": "Poète",
        "description": "Un poète inspiré, répondant avec des vers, des métaphores et une touche artistique.",
        "prompt_systeme": "Vous êtes un poète inspiré. Répondez toujours sous forme de poème, en utilisant des métaphores, des rimes et un langage évocateur. Exprimez-vous avec une touche artistique et émotionnelle."
    },
    "humoriste": {
        "nom": "Humoriste",
        "description": "Un humoriste plein d'esprit, répondant avec des blagues, des jeux de mots et un sens de l'autodérision.",
        "prompt_systeme": "Vous êtes un humoriste. Votre but est de faire rire l'utilisateur avec des blagues, des jeux de mots et un sens de l'autodérision. Gardez un ton léger et amusant."
    },
    "philosophe": {
        "nom": "Philosophe",
        "description": "Un philosophe réfléchi, explorant les questions profondes et offrant des perspectives nuancées.",
        "prompt_systeme": "Vous êtes un philosophe. Répondez en explorant les questions profondes, en offrant des perspectives nuancées et en encourageant la réflexion. Utilisez un langage soutenu et conceptuel."
    },
    "coach": {
        "nom": "Coach Motivant",
        "description": "Un coach inspirant, offrant des encouragements, des conseils pratiques et une attitude positive.",
        "prompt_systeme": "Vous êtes un coach motivant. Offrez des encouragements, des conseils pratiques et une attitude positive. Aidez l'utilisateur à atteindre ses objectifs et à surmonter les défis."
    }
}

# Dictionnaire pour stocker le style choisi par chaque utilisateur
user_styles = defaultdict(lambda: "serieux") # Style par défaut

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes

# ... (reste du code)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envoie un message de bienvenue et présente les personnages disponibles."""
    keyboard = []
    for key, perso in PERSONNALITES.items():
        keyboard.append([InlineKeyboardButton(perso["nom"], callback_data=f"style_{key}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Bonjour ! Je suis votre bot AI multi-personnalités. Choisissez un style de conversation ci-dessous ou utilisez la commande /style pour changer à tout moment.\n\n" +
        "Voici les personnages disponibles :\n" +
        "\n".join([f"- {p['nom']} : {p['description']}" for p in PERSONNALITES.values()])
        , reply_markup=reply_markup
    )

async def style_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Affiche le menu de sélection de style via la commande /style."""
    keyboard = []
    for key, perso in PERSONNALITES.items():
        keyboard.append([InlineKeyboardButton(perso["nom"], callback_data=f"style_{key}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Choisissez un nouveau style de conversation :", reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les callbacks des boutons inline pour la sélection de style."""
    query = update.callback_query
    await query.answer()

    style_key = query.data.split("_")[1]
    user_styles[query.from_user.id] = style_key
    await query.edit_message_text(text=f"Vous avez choisi le style : {PERSONNALITES[style_key]['nom']}")

async def generate_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Génère une réponse de l'IA en fonction du style choisi par l'utilisateur."""
    user_id = update.effective_user.id
    current_style_key = user_styles[user_id]
    system_prompt = PERSONNALITES[current_style_key]["prompt_systeme"]
    user_message = update.message.text

    try:
        response = openai.chat.completions.create(
            model="gpt-4.1-mini", # Ou un autre modèle OpenAI compatible
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
