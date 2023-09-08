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
from src.chatgpt import post, reply
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


@dp.message_handler(state=AvatarForm.gender)
async def command_enter_gender(message: Message, state: FSMContext) -> None:
    gender = message.text
    await state.update_data(gender=gender)
    await state.set_state(AvatarForm.age_group)
    await message.answer(
        "What age group for your avatar? (Options: Child, Young, Adult, Elderly)"
    )


@dp.message_handler(state=AvatarForm.age_group)
async def command_enter_age_group(message: Message, state: FSMContext) -> None:
    age_group = message.text
    await state.update_data(age_group=age_group)
    await state.set_state(AvatarForm.race)
    await message.answer(
        "Choose a race/ethnicity for your avatar? (Options: Caucasian, Asian, African, Hispanic, etc.)"
    )


@dp.message_handler(state=AvatarForm.race)
async def command_enter_race(message: Message, state: FSMContext) -> None:
    race = message.text
    await state.update_data(race=race)
    await state.set_state(AvatarForm.special_features)
    await message.answer("Any special features? (e.g., Tattoos, Scars, Glasses)")


@dp.message_handler(state=AvatarForm.special_features)
async def command_enter_special_features(message: Message, state: FSMContext) -> None:
    special_features = message.text
    await state.update_data(special_features=special_features)
    await state.set_state(AvatarForm.clothing_style)
    await message.answer("Any clothing style? (e.g., T-shirt, Hoodie)")


@dp.message_handler(state=AvatarForm.clothing_style)
async def command_enter_clothing_style(message: Message, state: FSMContext) -> None:
    clothing_style = message.text
    await state.update_data(special_features=clothing_style)
    await state.set_state(AvatarForm.emotion)
    await message.answer("Any special emotion? (e.g., Angry, Happy, Sad)")


@dp.message_handler(state=AvatarForm.emotion)
async def command_enter_emotion(message: Message, state: FSMContext) -> None:
    emotion = message.text
    await state.update_data(special_features=emotion)
    await state.set_state(AvatarForm.background)
    await message.answer("Any special background? (e.g., Forest, Black, Sea)")


# После последнего обработчика (background):
@dp.message_handler(state=AvatarForm.background)
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
        f"- Background: {data['background']}\n"
    )

    await message.reply_photo(photo=image_url, caption=caption)

    chat_id = message.chat.id
    with open(f"data/{chat_id}_avatar.yml", "w") as f:
        yaml.dump(data, f, default_flow_style=False)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
