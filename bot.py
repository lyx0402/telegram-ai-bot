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
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq API 地址
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# 存储用户对话历史（让AI记住上下文）
user_histories = {}

def call_groq(user_id, user_message):
    # 获取用户历史对话
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    # 添加用户消息
    user_histories[user_id].append({"role": "user", "content": user_message})
    
    # 只保留最近10条对话，避免超出限制
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": "你是一个聪明、有帮助的AI助手。用中文回答问题，回答要详细、有深度。"}
    ] + user_histories[user_id]
    
    data = {
        "model": "llama-3.1-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    response = requests.post(GROQ_API_URL, headers=headers, json=data)
    response.raise_for_status()
    reply = response.json()["choices"][0]["message"]["content"]
    
    # 保存AI回复到历史
    user_histories[user_id].append({"role": "assistant", "content": reply})
    
    return reply

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好！我是AI助手，由LLaMA 3.1 70B驱动，发消息给我吧！")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_histories[user_id] = []
    await update.message.reply_text("对话历史已清除！")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    try:
        reply = call_groq(user_id, user_message)
        # Telegram消息最长4096字符，超过就分段发送
        if len(reply) > 4000:
            for i in range(0, len(reply), 4000):
                await update.message.reply_text(reply[i:i+4000])
        else:
            await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("抱歉，出了点问题，请稍后再试。")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
