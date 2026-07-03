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
    """Crea las tablas si no existen. Se llama una vez al arrancar."""
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                contenido TEXT NOT NULL,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_notas_chat_id ON notas (chat_id)"
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


# --- Notas rápidas (Fase 4) ---

def guardar_nota(chat_id: int, contenido: str) -> int:
    """Guarda una nota nueva y devuelve su id."""
    with _conexion() as conn:
        cursor = conn.execute(
            "INSERT INTO notas (chat_id, contenido) VALUES (?, ?)",
            (chat_id, contenido),
        )
        return cursor.lastrowid


def listar_notas(chat_id: int) -> list[dict]:
    """Devuelve todas las notas de ese chat, más nuevas primero."""
    with _conexion() as conn:
        cursor = conn.execute(
            """
            SELECT id, contenido, creado_en FROM notas
            WHERE chat_id = ?
            ORDER BY id DESC
            """,
            (chat_id,),
        )
        filas = cursor.fetchall()

    return [
        {"id": id_, "contenido": contenido, "creado_en": creado_en}
        for id_, contenido, creado_en in filas
    ]


def borrar_nota(chat_id: int, nota_id: int) -> bool:
    """Borra una nota puntual por id. Devuelve True si existía y se borró."""
    with _conexion() as conn:
        cursor = conn.execute(
            "DELETE FROM notas WHERE chat_id = ? AND id = ?",
            (chat_id, nota_id),
        )
        return cursor.rowcount > 0
