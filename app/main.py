import asyncio
import logging
import os
import sys

import aioschedule as schedule
from aiogram import Bot, Dispatcher, types
from src import utils
from src.chatgpt import post, reply, summarize_in_batches
from src.prompts import (
    prompt_reply,
    prepromt,
    prompt_post,
    prompt_post_from_reply_direct,
)

# Logging
logger = logging.getLogger("AI-influencer")

# Set environment variables
cfg = utils.config("config/config.yaml")
utils.load_secrets("config/.env")

# Initialize Bot and dispatcher
bot = Bot(token=os.getenv("TG_TOKEN"))
dp = Dispatcher()

TIME = 60 * 60 * 12


async def send_periodic_message():
    try:
        post_about_shed = "Write random post about random topic based on your experience and science facts in AI, Machine Learning or Productivity"
        # post_text = summarize_in_batches(channel_post.reply_to_message.text, config=cfg)
        prepromt_text = prepromt()
        prompt_post_text = prompt_post(prepromt_text, post_about_shed)
        post_text = post(prompt_post_text, config=cfg)
        await bot.send_message(
            chat_id=os.getenv("TG_CHANNEL_ID"),
            text=post_text,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")


async def scheduler():
    schedule.every(TIME).seconds.do(send_periodic_message)
    while True:
        await schedule.run_pending()
        await asyncio.sleep(TIME)


async def on_startup(dp):
    """Set bot commands"""
    logger.info("Bot is starting up...")
    # asyncio.create_task(send_periodic_message())
    # asyncio.create_task(scheduler())


@dp.message(lambda message: message.reply_to_message is not None)
async def log_channel_comments(channel_post: types.Message):
    if channel_post.reply_to_message:
        if (
            channel_post.reply_to_message.sender_chat
            and channel_post.reply_to_message.sender_chat.type == "channel"
        ):
            logger.info(
                f"""Reply from {channel_post.from_user.username or channel_post.from_user.id} 
                To channel message {channel_post.reply_to_message.text}: {channel_post.text}"""
            )
            try:
                prepromt_text = prepromt()
                user_message = channel_post.text
                # post_text = summarize_in_batches(channel_post.reply_to_message.text, config=cfg)
                post_text = channel_post.reply_to_message.text
                username = channel_post.from_user.username
                prompt = prompt_reply(prepromt_text, user_message, post_text, username)
                chatgpt_response = reply(prompt, config=cfg)
                await bot.send_message(
                    chat_id=channel_post.chat.id,
                    text=chatgpt_response,
                    reply_to_message_id=channel_post.message_id,
                    parse_mode="Markdown",
                )
            except Exception as e:
                dev = cfg["developers"]
                msg = (
                    f"Sorry, I have internal problems. Please contact {', '.join(dev)}"
                )
                await channel_post.reply(msg)
                logger.error(e)


@dp.message(
    lambda message: message.forward_from_chat is not None
    and message.chat.type == "private"
)
async def forwarded_message_handler(message: types.Message):
    try:
        prepromt_text = prepromt()
        channel_name = message.forward_from_chat.title
        channel_id = message.forward_from_chat.username

        logger.info(
            f"FUNC forwarded_message_handler\n Reply from {channel_name}: @{channel_id}"
        )
        message_text = message.caption

        logger.info("User direct message:\n" + message_text)
        prompt_text = prompt_post_from_reply_direct(
            prepromt_text, message_text, channel_name, channel_id
        )
        new_post = post(prompt_text, config=cfg)

        logger.info("Post message:\n" + new_post)
        await bot.send_message(
            chat_id=os.getenv("TG_CHANNEL_ID"),
            text=new_post[:4096],
            parse_mode="Markdown",
        )
    except Exception as e:
        dev = cfg["developers"]
        msg = f"Sorry, I have internal problems. Please contact {', '.join(dev)}"
        await message.reply(msg)
        logger.error(e)


@dp.message(
    lambda message: message.forward_from_chat is None and message.chat.type == "private"
)
async def post_dir2blog(message: types.Message):
    """This handler will be called when user sends a direct message"""
    if message.chat.type != "private":
        return

    try:
        message_text = message.text
        logger.info("FUNC `post_dir2blog`\n User direct message:\n" + message_text)

        new_post = post(message_text, config=cfg)
        # new_post = "Глушилка на реплай из лички боту"

        await bot.send_message(
            chat_id=os.getenv("TG_CHANNEL_ID"),
            text=new_post[:4096],
            parse_mode="Markdown",
        )
    except Exception as e:
        dev = cfg["developers"]
        msg = f"Sorry, I have internal problems. Please contact {', '.join(dev)}"
        await message.reply(msg)
        logger.error(e)


async def main() -> None:
    await on_startup(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
