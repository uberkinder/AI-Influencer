import os

import openai
import tiktoken

from src.prompts import prepromt, summary_prompt


def reply(message: str, config: dict) -> str:
    # Generate response
    openai.api_key = os.getenv("OPENAI_API_KEY")
    role_promt = prepromt()
    chat_completion = openai.ChatCompletion.create(
        model=config["openai"]["model"],
        messages=[
            {"role": "system", "content": role_promt},
            {"role": "user", "content": message},
        ],
        temperature=config["openai"]["temperature"],
    )
    response = chat_completion["choices"][0]["message"]["content"]
    return response


def post(prompt: str, config: dict) -> str:
    # Generate response
    openai.api_key = os.getenv("OPENAI_API_KEY")
    role_promt = prepromt()
    chat_completion = openai.ChatCompletion.create(
        model=config["openai"]["model"],
        messages=[
            {"role": "system", "content": role_promt},
            {"role": "system", "content": prompt},
        ],
        temperature=config["openai"]["temperature"],
    )
    response = chat_completion["choices"][0]["message"]["content"]
    return response


def count_tokens(text: str, config: dict) -> int:
    """
    Count the number of tokens in a text string using tiktoken.
    """
    tokenizer = tiktoken.encoding_for_model(config["openai"]["model"])
    return len(tokenizer.encode(text))


def summarize_in_batches(text: str, config: dict, batch_size: int = 1000) -> list:
    """
    Summarize the text in batches if it exceeds the token limit.
    """
    # Check the number of tokens in the text
    total_tokens = count_tokens(text, config)
    openai.api_key = os.getenv("OPENAI_API_KEY")
    role_promt = prepromt()
    # If the text is within the token limit, just summarize it directly
    if total_tokens <= 4096:
        # Call ChatGPT to summarize the text
        chat_completion = openai.ChatCompletion.create(
            model=config["openai"]["model"],
            messages=[
                {"role": "system", "content": role_promt},
                {"role": "user", "content": summary_prompt(text)},
            ],
            temperature=config["openai"]["temperature"],
        )
        response = chat_completion["choices"][0]["message"]["content"]
        return response

    # If the text exceeds the token limit, split it into batches
    batches = [text[i : i + batch_size] for i in range(0, len(text), batch_size)]

    last_batch = ""
    summaries = []
    for batch in batches:
        # Call ChatGPT to summarize each batch

        chat_completion = openai.ChatCompletion.create(
            model=config["openai"]["model"],
            messages=[
                {"role": "system", "content": role_promt},
                {
                    "role": "user",
                    "content": summary_prompt(batch, len(batches), last_batch),
                },
            ],
            temperature=config["openai"]["temperature"],
        )
        last_batch = chat_completion["choices"][0]["message"]["content"]
        summaries.extend(last_batch)

    return "\n".join(summaries)
