# telegram-bot-ia

Bot de Telegram conversacional con IA — proyecto de aprendizaje por fases.

## Fases del proyecto

- [x] **Fase 0** — Setup del bot y del entorno
- [x] **Fase 1** — Bot "eco" funcionando
- [x] **Fase 2** — Conectar la respuesta a la API de Claude (este commit)
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

## Estado actual (Fase 2)

El bot manda cada mensaje de texto a la API de Claude y responde con lo
que la IA generó. Todavía **no tiene memoria**: cada mensaje se procesa
de forma independiente, sin contexto de mensajes anteriores. Eso es
la Fase 3.

Necesitás tener `ANTHROPIC_API_KEY` completo en tu `.env` para que
esta fase funcione.
