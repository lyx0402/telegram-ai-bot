
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from mistralai.client import MistralClient
from mistralai.models.chat_models import ChatMessage

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# 从环境变量获取 Telegram Bot Token 和 Mistral API Key
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN 环境变量未设置。")
    exit(1)
if not MISTRAL_API_KEY:
    logger.error("MISTRAL_API_KEY 环境变量未设置。")
    exit(1)

mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

async def start(update: Update, context) -> None:
    """发送用户在 /start 命令时收到的消息。"""
    user = update.effective_user
    await update.message.reply_html(
        f"你好，{user.mention_html()}! 我是一个由 Mistral AI 驱动的机器人。请给我发送消息，我将尽力回复你。",
    )

async def help_command(update: Update, context) -> None:
    """发送用户在 /help 命令时收到的消息。"""
    await update.message.reply_text("你可以给我发送任何消息，我将使用 Mistral AI 进行回复。")

async def echo(update: Update, context) -> None:
    """使用 Mistral AI 回复用户的消息。"""
    user_message = update.message.text
    logger.info(f"收到来自 {update.effective_user.full_name} 的消息: {user_message}")

    try:
        chat_response = mistral_client.chat(
            model="mistral-tiny", # 可以根据需要更改模型，例如 "mistral-small", "mistral-medium"
            messages=[
                ChatMessage(role="user", content=user_message)
            ]
        )
        ai_response = chat_response.choices[0].message.content
        await update.message.reply_text(ai_response)
        logger.info(f"回复 {update.effective_user.full_name}: {ai_response}")
    except Exception as e:
        logger.error(f"调用 Mistral AI API 失败: {e}")
        await update.message.reply_text("抱歉，Mistral AI 服务暂时无法响应。请稍后再试。")

def main() -> None:
    """启动机器人。"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 注册命令处理程序
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # 注册消息处理程序
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # 启动机器人
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
