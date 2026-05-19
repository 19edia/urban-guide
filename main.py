import logging
import os
import asyncio
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

# Configurar o logging para monitorar o comportamento do sistema
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente de um arquivo .env (útil para testes locais)
load_dotenv()

# --- Lógica Central do Jogo ---
def get_game_response(text: str, user_name: str) -> str:
    text = text.lower().strip()
    
    if text == "/start":
        return f"⚔️ Olá, {user_name}! Bem-vindo ao Reino. Use /help para ver os comandos."
    elif text == "/ping":
        return "Pong! 🏓 O servidor está rodando perfeitamente tanto na Web quanto no Telegram."
    elif text == "/help":
        return "📜 <b>Comandos:</b>\n/start - Iniciar\n/help - Ajuda\n/ping - Status"
    
    return f"Você disse: '{text}'. O mestre da guilda ainda está treinando os comandos de combate!"

# --- Handlers do Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name if update.effective_user else "Viajante"
    response = get_game_response("/start", user_name)
    await update.message.reply_html(response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = get_game_response("/help", "")
    await update.message.reply_html(response)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = get_game_response("/ping", "")
    await update.message.reply_text(response)

# --- Configuração do Bot e Servidor Web ---
token = os.getenv("TELEGRAM_TOKEN")
if not token:
    logger.error("TELEGRAM_TOKEN não configurado!")
    token = "dummy_token" # Evita quebrar o build do FastAPI antes de configurar o ENV

application = Application.builder().token(token).build()

# Registra os handlers de comando no Telegram
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("ping", ping))

@asynccontextmanager
async def lifespan(app: FastAPI):
    if token != "dummy_token":
        await application.initialize()
        await application.start()
        if application.updater:
            await application.updater.start_polling()
        logger.info("Bot Telegram iniciado.")
    else:
        logger.warning("Bot não iniciado: Token ausente.")
        
    yield
    
    if token != "dummy_token":
        if application.updater:
            await application.updater.stop()
        await application.stop()
        await application.shutdown()
        logger.info("Bot Telegram desligado.")

web_app = FastAPI(lifespan=lifespan)

# Rota principal para carregar a interface HTML
@web_app.get("/", response_class=HTMLResponse)
async def get_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Arquivo index.html não encontrado!</h1>"

if __name__ == "__main__":
    # O Render define automaticamente a porta através da variável de ambiente PORT
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(web_app, host="0.0.0.0", port=port)