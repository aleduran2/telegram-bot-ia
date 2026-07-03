# telegram-bot-ia

Bot de Telegram conversacional con IA — proyecto de aprendizaje por fases.

## Fases del proyecto

- [x] **Fase 0** — Setup del bot y del entorno
- [x] **Fase 1** — Bot "eco" funcionando
- [x] **Fase 2** — Conectar la respuesta a la API de Claude
- [x] **Fase 3** — Memoria de conversación
- [x] **Fase 4** — Primer "poder": notas rápidas vía tool use
- [x] **Fase 5** — Audio: voz a texto y texto a voz (este commit)
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

## Requisito adicional para la Fase 5: ffmpeg

La transcripción de audio (Whisper) necesita **ffmpeg** instalado como
programa del sistema, no alcanza con las librerías de Python.

**Windows:**
```powershell
winget install ffmpeg
```
Cerrá y volvé a abrir PowerShell después de instalarlo, y confirmá con:
```powershell
ffmpeg -version
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install ffmpeg
```

## Estado actual (Fase 5)

El bot ahora entiende **mensajes de voz** y puede **responder con audio**:

1. Le mandás un audio por Telegram
2. Whisper (corriendo local, sin API) lo transcribe a texto
3. Se procesa igual que un mensaje de texto (memoria + notas incluido)
4. Te responde en texto **y** en un mensaje de audio generado con gTTS

La primera vez que corras el bot después de esta fase, va a descargar
el modelo de Whisper (~150 MB) — puede tardar un rato, es normal.

Comandos disponibles:
- `/start` — mensaje de bienvenida
- `/reset` — borra la memoria de esa conversación y arranca de cero

Necesitás tener `ANTHROPIC_API_KEY` completo en tu `.env` y **ffmpeg
instalado en el sistema** (ver sección arriba) para que esta fase
funcione.
