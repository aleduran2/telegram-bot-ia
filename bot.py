"""
Fase 2 — Bot de Telegram conectado a Claude.

El bot recibe un mensaje de texto, se lo pasa a la API de Claude,
y responde con lo que la IA generó. Todavía SIN memoria: cada mensaje
se procesa de forma independiente (eso es la Fase 3).
"""

import logging
import os

from anthropic import Anthropic
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

claude = Anthropic(api_key=ANTHROPIC_API_KEY)

# Modelo a usar. Podés cambiarlo por otro si tenés acceso.
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "Sos un asistente personal que responde por Telegram. "
    "Respondé de forma breve, clara y en español, como en una charla de chat."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Se ejecuta cuando el usuario manda /start."""
    await update.message.reply_text(
        "¡Hola! Soy tu asistente con IA. Escribime lo que quieras y te respondo."
    )


async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manda el mensaje del usuario a Claude y devuelve la respuesta."""
    texto_usuario = update.message.text
    logger.info("Mensaje recibido de %s: %s", update.effective_user.id, texto_usuario)

    # Mientras Claude piensa, mostramos "escribiendo..." en Telegram
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        respuesta = claude.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": texto_usuario}],
        )
        texto_respuesta = respuesta.content[0].text
    except Exception:
        logger.exception("Error al llamar a la API de Claude")
        texto_respuesta = (
            "Uy, tuve un problema para pensar la respuesta. Probá de nuevo en un rato."
        )

    await update.message.reply_text(texto_respuesta)



def main() -> None:
    if not TELEGRAM_TOKEN:
        raise RuntimeError(
            "Falta TELEGRAM_TOKEN. Creá un archivo .env basado en .env.example"
        )

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    logger.info("Bot iniciado. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
