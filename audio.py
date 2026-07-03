"""
Fase 5 — Audio: voz a texto y texto a voz.

- Transcripción: Whisper corriendo localmente (sin API, sin costo).
  La primera vez que se usa, descarga el modelo (~150 MB para "base").
- Texto a voz: gTTS (Google Text-to-Speech), gratis y sin API key,
  pero necesita internet para generar el audio.

Requiere tener ffmpeg instalado en el sistema (no es una librería de
Python, es un programa aparte que Whisper usa para leer el audio).
"""

import logging

import whisper
from gtts import gTTS

logger = logging.getLogger(__name__)

# Modelo de Whisper a usar. Opciones de menor a mayor precisión (y peso):
# "tiny" < "base" < "small" < "medium" < "large"
# "base" es un buen balance para correr en CPU sin placa de video.
MODELO_WHISPER = "base"

# Cargamos el modelo una sola vez al importar el módulo, no en cada
# mensaje, porque cargarlo es lo que más tarda.
logger.info("Cargando modelo de Whisper (%s)... esto puede tardar la primera vez.", MODELO_WHISPER)
_modelo = whisper.load_model(MODELO_WHISPER)
logger.info("Modelo de Whisper listo.")


def transcribir_audio(ruta_archivo: str) -> str:
    """Recibe la ruta a un archivo de audio (.ogg, .mp3, etc.) y devuelve el texto."""
    resultado = _modelo.transcribe(ruta_archivo, language="es")
    return resultado["text"].strip()


def generar_audio(texto: str, ruta_salida: str) -> None:
    """Genera un archivo de audio a partir de texto y lo guarda en ruta_salida."""
    tts = gTTS(text=texto, lang="es")
    tts.save(ruta_salida)
