import logging
import sys
from aiogram import Bot, Dispatcher, types
from src import utils
from src.chatgpt import reply, post
import os
import asyncio

# Logging
logger = logging.getLogger("AI-influencer")

# Set environment variables
cfg = utils.config("config/config.yaml")
utils.load_secrets("config/.env")

# Initialize Bot and dispatcher
bot = Bot(token=os.getenv("TG_TOKEN"))
dp = Dispatcher()


async def send_periodic_message():
    while True:
        try:
            new_post = post(
                "Generate a new post on LLMs in your Telegram channel", config=cfg
            )
            await bot.send_message(
                chat_id=os.getenv("TG_CHANNEL_ID"),
                text=new_post,
            )
            await asyncio.sleep(15 * 60)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await asyncio.sleep(
                15 * 60
            )  # Wait for the next cycle even if an error occurs


async def on_startup(dp):
    """Set bot commands"""
    # Add the /start command to the list of bot commands
    logger.info("Bot is starting up...")
    asyncio.create_task(send_periodic_message())  # Start the repeated task


# Handler for solo messages
@dp.message()
async def echo_handler(message: types.Message):
    """This handler will be called when user sends a direct message"""
    try:
        response = reply(str(message.text), config=cfg)
        logger.info("ChatGPT response:\n" + response)
        await message.reply(response)

    except Exception as e:
        dev = cfg["developers"]
        msg = f"Sorry, I have internal problems. Please contact {dev}"
        await message.reply(msg)
        logger.error(e)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
