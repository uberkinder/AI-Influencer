import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from src import utils
import openai
import os

# Logging
logging.config.fileConfig("logging_config.ini")
logger = logging.getLogger("AI-influencer")

# Set environment variables
utils.load_secrets("./config/.env.yaml")
cfg = utils.config("./config/config.yaml")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize bot and dispatcher
bot = Bot(token=os.getenv("TG_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def on_startup(dp):
    """Set bot commands"""
    # Add the /start command to the list of bot commands
    logger.info("Bot is starting up...")
    pass


# Handler for solo messages
@dp.message_handler()
async def echo(message: types.Message):
    """This handler will be called when user sends a direct message"""
    try:
        # Generate response
        chat_completion = openai.ChatCompletion.create(
            model=cfg["openai"]["model"],
            messages=[
                {"role": "system", "content": cfg["openai"]["role"]},
                {"role": "user", "content": message.text},
            ],
            temperature=cfg["openai"]["temperature"],
        )
        response = chat_completion["choices"][0]["message"]["content"]
        logger.info("ChatGPT response:\n" + response)

        await message.reply(response)

    except Exception as e:
        dev = cfg['developers']
        msg = f"Sorry, I have internal problems. Please contact {dev}"
        await message.reply(msg)
        logger.error(e)


if __name__ == "__main__":
    # Start the bot
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
