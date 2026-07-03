"""
Fase 4 — Bot de Telegram con memoria + notas rápidas vía tool use.

Este es el primer "poder" real del bot: le damos a Claude herramientas
(funciones) que puede decidir usar según lo que le escribas. Por ejemplo,
si le decís "anotá que tengo que llamar al dentista", Claude va a elegir
solo usar la herramienta guardar_nota. Si le preguntás "¿qué notas
tengo?", va a usar listar_notas. Si solo charlás, no usa ninguna.

Esto es "tool use" / function calling: el mecanismo central detrás de
los agentes de IA.

Comandos:
  /start  - mensaje de bienvenida
  /reset  - borra la memoria de esa conversación y arranca de cero
"""

import json
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

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "Sos un asistente personal que responde por Telegram. "
    "Respondé de forma breve, clara y en español, como en una charla de chat. "
    "Tenés memoria de los mensajes anteriores de esta conversación. "
    "Tenés herramientas para guardar y listar notas rápidas del usuario: "
    "usalas cuando la persona te pida anotar algo, guardar una idea, o "
    "consultar sus notas. No uses herramientas si el mensaje es solo charla."
)

# --- Definición de las herramientas que Claude puede usar ---

TOOLS = [
    {
        "name": "guardar_nota",
        "description": (
            "Guarda una nota rápida del usuario para consultar después. "
            "Usala cuando la persona te pida anotar, recordar o guardar algo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contenido": {
                    "type": "string",
                    "description": "El texto de la nota a guardar.",
                }
            },
            "required": ["contenido"],
        },
    },
    {
        "name": "listar_notas",
        "description": "Devuelve todas las notas guardadas por el usuario.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


def ejecutar_herramienta(nombre: str, entrada: dict, chat_id: int) -> str:
    """
    Ejecuta la función real correspondiente a la herramienta que Claude
    pidió usar, y devuelve un resultado en texto para mandarle de vuelta.
    """
    if nombre == "guardar_nota":
        contenido = entrada["contenido"]
        nota_id = memoria.guardar_nota(chat_id, contenido)
        return f"Nota #{nota_id} guardada: {contenido}"

    if nombre == "listar_notas":
        notas = memoria.listar_notas(chat_id)
        if not notas:
            return "No hay notas guardadas todavía."
        lineas = [f"#{n['id']}: {n['contenido']}" for n in notas]
        return "\n".join(lineas)

    return f"Herramienta desconocida: {nombre}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hola! Soy tu asistente con IA. Tengo memoria de la charla y puedo "
        "guardarte notas rápidas — solo pedímelo con tus palabras, por ejemplo "
        "\"anotá que tengo que comprar leche\" o \"¿qué notas tengo?\".\n\n"
        "Si querés que me olvide de la charla, mandá /reset."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    memoria.borrar_historial(chat_id)
    await update.message.reply_text("Listo, me olvidé de todo lo que hablamos hasta ahora.")


async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    texto_usuario = update.message.text
    logger.info("Mensaje recibido de %s: %s", chat_id, texto_usuario)

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    memoria.guardar_mensaje(chat_id, "user", texto_usuario)
    historial = memoria.obtener_historial(chat_id)

    try:
        texto_respuesta = await procesar_con_claude(historial, chat_id)
        memoria.guardar_mensaje(chat_id, "assistant", texto_respuesta)
    except Exception:
        logger.exception("Error al llamar a la API de Claude")
        texto_respuesta = (
            "Uy, tuve un problema para pensar la respuesta. Probá de nuevo en un rato."
        )

    await update.message.reply_text(texto_respuesta)


async def procesar_con_claude(historial: list[dict], chat_id: int) -> str:
    """
    Llama a Claude con el historial y las herramientas disponibles.
    Si Claude decide usar una herramienta, la ejecutamos, le devolvemos
    el resultado, y le pedimos que arme la respuesta final. Este ida y
    vuelta es el "loop de tool use".
    """
    mensajes = list(historial)

    respuesta = claude.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=mensajes,
    )

    # Mientras Claude siga pidiendo usar herramientas, se las damos y
    # le devolvemos el resultado, hasta que decida responder en texto.
    while respuesta.stop_reason == "tool_use":
        mensajes.append({"role": "assistant", "content": respuesta.content})

        resultados_herramientas = []
        for bloque in respuesta.content:
            if bloque.type == "tool_use":
                logger.info("Claude pidió usar la herramienta: %s(%s)", bloque.name, bloque.input)
                resultado = ejecutar_herramienta(bloque.name, bloque.input, chat_id)
                resultados_herramientas.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": bloque.id,
                        "content": resultado,
                    }
                )

        mensajes.append({"role": "user", "content": resultados_herramientas})

        respuesta = claude.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=mensajes,
        )

    # Extraemos el texto final de la respuesta
    partes_texto = [bloque.text for bloque in respuesta.content if bloque.type == "text"]
    return "\n".join(partes_texto) if partes_texto else "..."


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
