"""
Fase 3 — Memoria de conversación con SQLite.

Guarda cada mensaje (de usuario o del asistente) asociado a un chat_id,
para que el bot pueda recordar el contexto de la conversación entre
reinicios del proceso.
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "conversaciones.db"

# Cuántos mensajes previos (usuario + asistente) mandamos a Claude como
# contexto. Subirlo da más memoria pero gasta más tokens por mensaje.
MAX_MENSAJES_CONTEXTO = 20


@contextmanager
def _conexion():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def inicializar_db() -> None:
    """Crea la tabla de mensajes si no existe. Se llama una vez al arrancar."""
    with _conexion() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                rol TEXT NOT NULL CHECK (rol IN ('user', 'assistant')),
                contenido TEXT NOT NULL,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mensajes_chat_id ON mensajes (chat_id)"
        )


def guardar_mensaje(chat_id: int, rol: str, contenido: str) -> None:
    """Guarda un mensaje (de usuario o asistente) en la base."""
    with _conexion() as conn:
        conn.execute(
            "INSERT INTO mensajes (chat_id, rol, contenido) VALUES (?, ?, ?)",
            (chat_id, rol, contenido),
        )


def obtener_historial(chat_id: int) -> list[dict]:
    """
    Devuelve los últimos N mensajes de esa conversación, en formato
    listo para mandarle a la API de Claude:
    [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    with _conexion() as conn:
        cursor = conn.execute(
            """
            SELECT rol, contenido FROM mensajes
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (chat_id, MAX_MENSAJES_CONTEXTO),
        )
        filas = cursor.fetchall()

    # Los traemos en orden descendente (más nuevo primero) para el LIMIT,
    # pero Claude necesita el orden cronológico real.
    filas.reverse()
    return [{"role": rol, "content": contenido} for rol, contenido in filas]


def borrar_historial(chat_id: int) -> None:
    """Borra toda la conversación de un chat (por ejemplo, con /reset)."""
    with _conexion() as conn:
        conn.execute("DELETE FROM mensajes WHERE chat_id = ?", (chat_id,))
