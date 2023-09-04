import openai
import os


def reply(message: str, config: dict) -> str:
    # Generate response
    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = "Reply to user like if you are very busy making AGI"
    chat_completion = openai.Completion.create(
        model=config["openai"]["model"],
        messages=[
            {"role": "system", "content": config["bot"]["role"]},
            {"role": "system", "content": prompt},
            {"role": "user", "content": message},
        ],
        temperature=config["openai"]["temperature"],
    )
    response = chat_completion["choices"][0]["text"]
    return response


def post(prompt: str, config: dict) -> str:
    # Generate response
    openai.api_key = os.getenv("OPENAI_API_KEY")
    chat_completion = openai.ChatCompletion.create(
        model=config["openai"]["model"],
        messages=[
            {"role": "system", "content": config["bot"]["role"]},
            {"role": "system", "content": prompt},
        ],
        temperature=config["openai"]["temperature"],
    )
    response = chat_completion["choices"][0]["message"]["content"]
    return response
