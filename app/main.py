import asyncio
import datetime
import logging
import os
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from src import utils
from src.chatgpt import post, reply

# Logging
logger = logging.getLogger("AI-influencer")

# Set environment variables
cfg = utils.config("config/config.yaml")
utils.load_secrets("config/.env")

# Initialize Bot and dispatcher
bot = Bot(token=os.getenv("TG_TOKEN"))
dp = Dispatcher()

chat_schedules = {}


chat_schedules = {}


async def send_daily_message(chat_id, time_str):
    while True:
        new_post = post(
            "Generate a new post on LLMs in your Telegram channel", config=cfg
        )
        now = datetime.now()
        target_time = now.replace(
            hour=int(time_str.split(":")[0]),
            minute=int(time_str.split(":")[1]),
            second=0,
            microsecond=0,
        )

        if target_time < now:
            target_time += timedelta(days=1)

        delta_seconds = (target_time - now).total_seconds()

        logger.info(f"Sleeping for {delta_seconds} seconds.")
        await asyncio.sleep(delta_seconds)

        await bot.send_message(chat_id, new_post)
        logger.info(f"Message sent to {chat_id} at {time_str}.")


@dp.message(Command("set_schedule"))
async def set_user_schedule(message: types.Message):
    chat_id = message.chat.id
    text = message.text.split()

    if len(text) < 2:
        await message.reply(
            "Please provide the times. E.g. /set_schedule 09:00 12:30 18:45"
        )
        return

    time_list = text[1:]

    # Cancel existing schedules for this chat
    if chat_id in chat_schedules:
        for task in chat_schedules[chat_id]:
            task.cancel()

    chat_schedules[chat_id] = []

    for time_str in time_list:
        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError("Invalid time format")

            task = asyncio.create_task(send_daily_message(chat_id, time_str))
            chat_schedules[chat_id].append(task)

        except ValueError:
            await message.reply("Invalid time format. Use HH:MM.")
            return

    await message.reply(f"Schedule set for times: {', '.join(time_list)}")


async def on_startup(dp):
    """Set bot commands"""
    # Add the /start command to the list of bot commands
    logger.info("Bot is starting up...")


# Handler for solo messages
@dp.message()
async def echo_handler(message: types.Message):
    """This handler will be called when user sends a direct message"""
    try:
        message_text = message.text
        logger.info("User direct message:\n" + message_text)
        response = reply(message_text, config=cfg)
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
