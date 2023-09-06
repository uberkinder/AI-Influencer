import asyncio
import logging
import os
import sys

#sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))
from aiogram import Bot, Dispatcher, types
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

TIME = 30


async def send_periodic_message():
    while True:
        try:
            # new_post = post(
            #    "Generate a new post on LLMs in your Telegram channel", config=cfg
            # )
            new_post = "Глушилка на шедулер"
            logger.info("SHEDDULING MESSAGE \n" + new_post)
            await bot.send_message(
                chat_id=os.getenv("TG_CHANNEL_ID"),
                text=new_post,
            )
            await asyncio.sleep(TIME)
        except Exception as e:
            logger.error("Error sending message: {e}")
            await asyncio.sleep(TIME)


async def on_startup(dp):
    """Set bot commands"""
    # Add the /start command to the list of bot commands
    logger.info("Bot is starting up...")
    asyncio.create_task(send_periodic_message())  # Start the repeated task


@dp.message(lambda message: message.reply_to_message is not None)
async def log_channel_comments(channel_post: types.Message):
    if channel_post.reply_to_message:
        # Если это ответ на сообщение из канала
        if (
            channel_post.reply_to_message.sender_chat
            and channel_post.reply_to_message.sender_chat.type == "channel"
        ):
            logger.info(
                f"Reply from {channel_post.from_user.username or channel_post.from_user.id} to channel message {channel_post.reply_to_message.text}: {channel_post.text}"
            )
            try:
                user_message = channel_post.text
                chatgpt_response = reply(user_message, config=cfg)
                #chatgpt_response = "Заглушка на реплай"
                await bot.send_message(
                    chat_id=channel_post.chat.id,
                    text=chatgpt_response,
                    reply_to_message_id=channel_post.message_id,
                )
            except Exception as e:
                dev = cfg["developers"]
                msg = (
                    f"Sorry, I have internal problems. Please contact {', '.join(dev)}"
                )
                await channel_post.reply(msg)
                logger.error(e)


@dp.message()
async def post_dir2blog(message: types.Message):
    """This handler will be called when user sends a direct message"""
    if message.chat.type != "private":
        return

    try:
        message_text = message.text        
        logger.info("User direct message:\n" + message_text)

        new_post = post(message_text, config=cfg)
        # new_post = "Глушилка на реплай из лички боту"

        await bot.send_message(
            chat_id=os.getenv("TG_CHANNEL_ID"),
            text=new_post[:4096],
        )
        # await bot.send_message(
        #     chat_id=os.getenv("TG_CHANNEL_ID"),
        #     text=new_post[4096:],
        # )
    except Exception as e:
        dev = cfg["developers"]
        msg = f"Sorry, I have internal problems. Please contact {', '.join(dev)}"
        await message.reply(msg)
        logger.error(e)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
