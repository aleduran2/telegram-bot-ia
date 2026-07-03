"""
Fase 3 — Bot de Telegram conectado a Claude, con memoria de conversación.

El bot recibe un mensaje, lo guarda en SQLite, arma el historial de esa
conversación y se lo manda a Claude como contexto. Así el bot recuerda
lo que hablaron antes, incluso si reiniciás el proceso.

Comandos:
  /start  - mensaje de bienvenida
  /reset  - borra la memoria de esa conversación y arranca de cero
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

import memoria

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
    "Respondé de forma breve, clara y en español, como en una charla de chat. "
    "Tenés memoria de los mensajes anteriores de esta conversación."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Se ejecuta cuando el usuario manda /start."""
    await update.message.reply_text(
        "¡Hola! Soy tu asistente con IA y ahora tengo memoria de nuestra charla. "
        "Escribime lo que quieras. Si querés que me olvide de todo, mandá /reset."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Borra el historial de esta conversación."""
    chat_id = update.effective_chat.id
    memoria.borrar_historial(chat_id)
    await update.message.reply_text("Listo, me olvidé de todo lo que hablamos hasta ahora.")


async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Guarda el mensaje, arma el historial y le pregunta a Claude con contexto."""
    chat_id = update.effective_chat.id
    texto_usuario = update.message.text
    logger.info("Mensaje recibido de %s: %s", chat_id, texto_usuario)

    # Mientras Claude piensa, mostramos "escribiendo..." en Telegram
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Guardamos el mensaje del usuario ANTES de llamar a la API,
    # así queda registrado aunque la llamada falle.
    memoria.guardar_mensaje(chat_id, "user", texto_usuario)

    historial = memoria.obtener_historial(chat_id)

    try:
        respuesta = claude.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=historial,
        )
        texto_respuesta = respuesta.content[0].text
        # Guardamos también la respuesta del asistente, para que el
        # próximo mensaje tenga el contexto completo de ida y vuelta.
        memoria.guardar_mensaje(chat_id, "assistant", texto_respuesta)
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

    memoria.inicializar_db()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    logger.info("Bot iniciado. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
