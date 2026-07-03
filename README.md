# telegram-bot-ia

Bot de Telegram conversacional con IA — proyecto de aprendizaje por fases.

## Fases del proyecto

- [x] **Fase 0** — Setup del bot y del entorno
- [x] **Fase 1** — Bot "eco" funcionando
- [x] **Fase 2** — Conectar la respuesta a la API de Claude
- [x] **Fase 3** — Memoria de conversación (este commit)
- [ ] **Fase 3** — Memoria de conversación
- [ ] **Fase 4** — Primer "poder" (recordatorios / notas / consulta de datos)
- [ ] **Fase 5** — Entrada/salida por audio (speech-to-text / text-to-speech)

## Cómo correrlo

1. Cloná el repo y entrá a la carpeta:
   ```bash
   git clone https://github.com/aleduran2/telegram-bot-ia.git
   cd telegram-bot-ia
   ```

2. Creá el entorno virtual e instalá dependencias:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # en Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copiá `.env.example` a `.env` y completá tu token:
   ```bash
   cp .env.example .env
   ```
   Editá `.env` y poné el token que te dio @BotFather en `TELEGRAM_TOKEN`.

4. Corré el bot:
   ```bash
   python bot.py
   ```

5. Andá a Telegram, abrí tu bot y mandale `/start` o cualquier mensaje de texto.

## Estado actual (Fase 3)

El bot ahora tiene **memoria de conversación** guardada en SQLite
(`conversaciones.db`, se crea sola al arrancar). Cada mensaje tuyo y
cada respuesta del bot se guardan asociados a tu chat de Telegram, y
en cada mensaje nuevo se le manda a Claude el historial reciente como
contexto — así el bot recuerda cosas que le dijiste antes, incluso si
reiniciás el proceso.

Comandos disponibles:
- `/start` — mensaje de bienvenida
- `/reset` — borra la memoria de esa conversación y arranca de cero

Necesitás tener `ANTHROPIC_API_KEY` completo en tu `.env` para que
esta fase funcione.
