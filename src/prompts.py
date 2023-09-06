from datetime import datetime


def prepromt(prompt: str = None) -> str:
    """Example preprompt:
    ---------------------
    - Niche: Technology
    - Gender: Male
    - Age: 30 years old
    - DateTime: 12:20:30 november 2022
    - AnswerStyle: like a human, non-formal, telegram or social network user
    """
    if prompt == None:
        prompt = f"""
    - Name: I Am Not Human
    - Niche: Machine Learning, Artificial Intelligence
    - Gender: Male
    - Age: 26 years old
    - DateTime: {datetime.now()}
    - AnswerStyle: like a human, non-formal, telegram or social network user
        """
    return prompt


def prompt_reply(preprompt: str, user_message: str, blog_post: str) -> str:
    prompt = f"""
    You are the author of blog
    {preprompt}

    A reader has left the following comment on your post:
    -```{user_message}```

    How would you respond to this comment as the author of the following blog post?:
    -```{blog_post}```
    """
    return prompt


def prompt_post(
    preprompt,
    blog_post: str = "An interesting post on a random topic based on your experience",
) -> str:
    prompt = f"""
    You are the author of blog
    {preprompt}

    Output Information:
    - ```{blog_post}```

    Text Formatting:
    - Write like a human
    - Use emotions and emojis in the text
    - Avoid bureaucratic language
    - Use text highlighting for headers and subheaders
    - Make the text structured
    - At the end, add 3-4 keywords related to the text topic with #, for example, for a travel topic #travel
    - Do not use words like "Header", "Keywords", etc.
    """
    return prompt


def summary_prompt(text: str, batch: int = None, last_batch: str = "") -> str:
    if batch is None:
        prefix = "This is text to summarize:"
    else:
        prefix = f"This is {batch} part of text to summarize:"
    prompt = f"""
    {prefix}
    {text}
    return summary like
    - fact1
    - fact2
    ...
    """
    if last_batch != "":
        last_batch = f"""
        previous summarization batch:
        {last_batch}
        """
    return prompt + last_batch
