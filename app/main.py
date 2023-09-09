import asyncio
import datetime
import logging
import os
import sys
from datetime import datetime, timedelta

import requests
import yaml
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from src import utils
from src.chatgpt import post, reply, summarize_in_batches
from src.prompts import (
    prepromt,
    prompt_post,
    prompt_post_from_reply_direct,
    prompt_reply,
)
from src.text2image import create_avatar_prompt, fetch_image

from form import AvatarForm

# Logging
logger = logging.getLogger("AI-influencer")

# Set environment variables
cfg = utils.config("config/config.yaml")
utils.load_secrets("config/.env")

# Initialize Bot and dispatcher
bot = Bot(token=os.getenv("TG_TOKEN"))
dp = Dispatcher()
form_router = Router()
dp.include_router(form_router)

chat_schedules = {}


async def make_random_post():
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


async def send_daily_message(chat_id, time_str):
    while True:
        new_post = make_random_post()
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


@dp.message(Command("start"))
async def start_bot(message: types.Message):
    welcome_message = (
        "Welcome to the bot! 🤖\n\n"
        "Here's what you can do:\n"
        "- Use /create_avatar to answer a few questions and create your avatar.\n\n"
        "- Use /set_schedule to set a schedule. E.g.,\n `/set_schedule 09:00 12:30 18:45`\n\n"
        "Type any message to continue."
    )

    await message.reply(welcome_message)


@dp.message(Command("create_avatar"))
async def command_start_avatar(message: Message, state: FSMContext) -> None:
    await state.set_state(AvatarForm.gender)
    await message.answer(
        "What gender would you like for your avatar? (Options: Male, Female, Non-binary)",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(AvatarForm.gender)
async def command_enter_gender(message: Message, state: FSMContext) -> None:
    gender = message.text
    await state.update_data(gender=gender)
    await state.set_state(AvatarForm.age_group)
    await message.answer(
        "What age group for your avatar? (Options: Child, Young, Adult, Elderly)"
    )


@form_router.message(AvatarForm.age_group)
async def command_enter_age_group(message: Message, state: FSMContext) -> None:
    age_group = message.text
    await state.update_data(age_group=age_group)
    await state.set_state(AvatarForm.race)
    await message.answer(
        "Choose a race/ethnicity for your avatar? (Options: Caucasian, Asian, African, Hispanic, etc.)"
    )


@form_router.message(AvatarForm.race)
async def command_enter_race(message: Message, state: FSMContext) -> None:
    race = message.text
    await state.update_data(race=race)
    await state.set_state(AvatarForm.special_features)
    await message.answer("Any special features? (e.g., Tattoos, Scars, Glasses)")


@form_router.message(AvatarForm.special_features)
async def command_enter_special_features(message: Message, state: FSMContext) -> None:
    special_features = message.text
    await state.update_data(special_features=special_features)
    await state.set_state(AvatarForm.clothing_style)
    await message.answer("Any clothing style? (e.g., T-shirt, Hoodie)")


@form_router.message(AvatarForm.clothing_style)
async def command_enter_clothing_style(message: Message, state: FSMContext) -> None:
    clothing_style = message.text
    await state.update_data(clothing_style=clothing_style)
    await state.set_state(AvatarForm.emotion)
    await message.answer("Any special emotion? (e.g., Angry, Happy, Sad)")


@form_router.message(AvatarForm.emotion)
async def command_enter_emotion(message: Message, state: FSMContext) -> None:
    emotion = message.text
    await state.update_data(emotion=emotion)
    await state.set_state(AvatarForm.style)
    await message.answer("Any special style? (e.g., Anime, Cartoon, Pixel)")


@form_router.message(AvatarForm.style)
async def command_enter_style(message: Message, state: FSMContext) -> None:
    style = message.text
    await state.update_data(style=style)
    await state.set_state(AvatarForm.background)
    await message.answer("Any special background? (e.g., Forest, Black, Sea)")


# После последнего обработчика (background):
@form_router.message(AvatarForm.background)
async def command_enter_background(message: Message, state: FSMContext) -> None:
    background = message.text
    await state.update_data(background=background)

    data = await state.get_data()
    await state.clear()
    image_url = await fetch_image(create_avatar_prompt(data))

    caption = (
        f"Here's what you selected for your avatar:\n"
        f"- Gender: {data['gender']}\n"
        f"- Age Group: {data['age_group']}\n"
        f"- Race: {data['race']}\n"
        f"- Special Features: {data['special_features']}\n"
        f"- Clothing Style: {data['clothing_style']}\n"
        f"- Emotion: {data['emotion']}\n"
        f"- Style: {data['style']}\n"
        f"- Background: {data['background']}\n"
    )

    await message.reply_photo(photo=image_url, caption=caption)

    chat_id = message.chat.id
    with open(f"data/{chat_id}_avatar.yml", "w") as f:
        yaml.dump(data, f, default_flow_style=False)


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
