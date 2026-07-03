"""
Fase 5 — Bot de Telegram con memoria, notas rápidas y audio (voz a voz).

Adhiere todo lo de las fases anteriores y suma:
  - Si le mandás un audio, lo transcribe (Whisper local) y lo procesa
    como si fuera un mensaje de texto.
  - Te responde con un mensaje de audio generado (gTTS), además del texto.

Comandos:
  /start  - mensaje de bienvenida
  /reset  - borra la memoria de esa conversación y arranca de cero
"""

import logging
import os
import tempfile

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

import audio
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
    "consultar sus notas. No uses herramientas si el mensaje es solo charla. "
    "Algunos de tus mensajes te llegan transcriptos desde audio, así que "
    "pueden tener pequeños errores de transcripción; interpretalos con sentido común."
)

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
        "¡Hola! Soy tu asistente con IA. Tengo memoria de la charla, puedo "
        "guardarte notas rápidas, y ahora también entiendo audios y te "
        "puedo responder con voz.\n\n"
        "Si querés que me olvide de la charla, mandá /reset."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    memoria.borrar_historial(chat_id)
    await update.message.reply_text("Listo, me olvidé de todo lo que hablamos hasta ahora.")


def procesar_con_claude(historial: list[dict], chat_id: int) -> str:
    """
    Llama a Claude con el historial y las herramientas disponibles.
    Si Claude decide usar una herramienta, la ejecutamos, le devolvemos
    el resultado, y le pedimos que arme la respuesta final.
    """
    mensajes = list(historial)

    respuesta = claude.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=mensajes,
    )

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

    partes_texto = [bloque.text for bloque in respuesta.content if bloque.type == "text"]
    return "\n".join(partes_texto) if partes_texto else "..."


def generar_respuesta(chat_id: int, texto_usuario: str) -> str:
    """Guarda el mensaje del usuario, arma el historial y obtiene la respuesta de Claude."""
    memoria.guardar_mensaje(chat_id, "user", texto_usuario)
    historial = memoria.obtener_historial(chat_id)

    try:
        texto_respuesta = procesar_con_claude(historial, chat_id)
        memoria.guardar_mensaje(chat_id, "assistant", texto_respuesta)
    except Exception:
        logger.exception("Error al llamar a la API de Claude")
        texto_respuesta = (
            "Uy, tuve un problema para pensar la respuesta. Probá de nuevo en un rato."
        )

    return texto_respuesta


async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja un mensaje de texto normal."""
    chat_id = update.effective_chat.id
    texto_usuario = update.message.text
    logger.info("Mensaje de texto recibido de %s: %s", chat_id, texto_usuario)

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    texto_respuesta = generar_respuesta(chat_id, texto_usuario)
    await update.message.reply_text(texto_respuesta)


async def responder_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja un mensaje de voz: lo transcribe, lo procesa, y responde en texto + audio."""
    chat_id = update.effective_chat.id

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    with tempfile.TemporaryDirectory() as carpeta_temp:
        ruta_ogg = os.path.join(carpeta_temp, "entrada.ogg")
        ruta_mp3 = os.path.join(carpeta_temp, "salida.mp3")

        archivo_voz = await context.bot.get_file(update.message.voice.file_id)
        await archivo_voz.download_to_drive(ruta_ogg)

        logger.info("Transcribiendo audio de %s...", chat_id)
        texto_usuario = audio.transcribir_audio(ruta_ogg)
        logger.info("Transcripción: %s", texto_usuario)

        if not texto_usuario:
            await update.message.reply_text(
                "No pude entender el audio, ¿podés intentar de nuevo?"
            )
            return

        # Mostramos qué entendió, para que puedas notar errores de transcripción
        await update.message.reply_text(f"🎙️ Escuché: \"{texto_usuario}\"")

        texto_respuesta = generar_respuesta(chat_id, texto_usuario)

        # Respondemos en texto...
        await update.message.reply_text(texto_respuesta)

        # ...y también en audio.
        try:
            audio.generar_audio(texto_respuesta, ruta_mp3)
            with open(ruta_mp3, "rb") as f:
                await context.bot.send_audio(chat_id=chat_id, audio=f)
        except Exception:
            logger.exception("No se pudo generar/enviar el audio de respuesta")


def main() -> None:
    if not TELEGRAM_TOKEN:
        raise RuntimeError(
            "Falta TELEGRAM_TOKEN. Creá un archivo .env basado en .env.example"
        )

    memoria.inicializar_db()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.VOICE, responder_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))

    logger.info("Bot iniciado. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
