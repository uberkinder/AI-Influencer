import asyncio
import datetime
import logging
import os
import sys
from datetime import datetime, timedelta

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

from form import UserForm

sys.path.append("../../")
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
        "- Use /create to answer a few questions and create your profile.\n\n"
        "- Use /set_schedule to set a schedule. E.g.,\n `/set_schedule 09:00 12:30 18:45`\n\n"
        "Type any message to continue."
    )

    await message.reply(welcome_message)


@dp.message(Command("create"))
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(UserForm.name)
    await message.answer(
        "Hi there! What's your name?",
        reply_markup=ReplyKeyboardRemove(),
    )


# @form_router.message(Command("cancel"))
# @form_router.message(F.text.casefold() == "cancel")
# async def cancel_handler(message: Message, state: FSMContext) -> None:
#     """
#     Allow user to cancel any action
#     """
#     current_state = await state.get_state()
#     if current_state is None:
#         return

#     logging.info("Cancelling state %r", current_state)
#     await state.clear()
#     await message.answer(
#         "Cancelled.",
#         reply_markup=ReplyKeyboardRemove(),
#     )


@form_router.message(UserForm.name)
async def command_enter_name(message: Message, state: FSMContext) -> None:
    user_name = message.text
    print()
    await state.update_data(name=user_name)  # Save name
    # await UserForm.next()  # Go to the next state
    await state.set_state(UserForm.age)
    await message.answer("Great! How old are you?")


@form_router.message(UserForm.age)
async def command_enter_age(message: Message, state: FSMContext) -> None:
    user_age = message.text  # assume the user enters a number
    await state.update_data(age=user_age)  # Save age
    data = await state.get_data()
    await state.clear()  # Clear the state

    await message.answer(
        f"Great, here is what you told me:\n"
        f"- Name: {data['name']}\n"
        f"- Age: {data['age']}\n"
    )
    chat_id = message.chat.id
    with open(f"data/{chat_id}.yml", "w") as f:
        yaml.dump(data, f, default_flow_style=False)


# # Handler for solo messages
# @dp.message()
# async def echo_handler(message: types.Message):
#     """This handler will be called when user sends a direct message"""
#     try:
#         message_text = message.text
#         logger.info("User direct message:\n" + message_text)
#         response = reply(message_text, config=cfg)
#         logger.info("ChatGPT response:\n" + response)
#         await message.reply(response)

#     except Exception as e:
#         dev = cfg["developers"]
#         msg = f"Sorry, I have internal problems. Please contact {dev}"
#         await message.reply(msg)
#         logger.error(e)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
