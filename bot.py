"""
Fase 1 — Bot "eco" de Telegram.

Objetivo de esta fase: confirmar que la plomería básica funciona.
El bot recibe un mensaje de texto y responde repitiéndolo.
En la Fase 2 vamos a reemplazar la lógica de respuesta por una llamada
a la API de Claude.
"""

import logging
import os

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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Se ejecuta cuando el usuario manda /start."""
    await update.message.reply_text(
        "¡Hola! Soy tu bot de prueba. Escribime cualquier cosa y te la repito."
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde repitiendo el mensaje que llegó."""
    texto_usuario = update.message.text
    logger.info("Mensaje recibido de %s: %s", update.effective_user.id, texto_usuario)
    await update.message.reply_text(f"Dijiste: {texto_usuario}")


def main() -> None:
    if not TELEGRAM_TOKEN:
        raise RuntimeError(
            "Falta TELEGRAM_TOKEN. Creá un archivo .env basado en .env.example"
        )

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("Bot iniciado. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
