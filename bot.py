
import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量获取密钥
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Mistral API 地址
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def call_mistral(user_message):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好！我是AI助手，发消息给我吧！")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        reply = call_mistral(user_message)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("抱歉，出了点问题，请稍后再试。")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
