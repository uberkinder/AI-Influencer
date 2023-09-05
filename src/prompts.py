def add_tags_prompt() -> str:
    return "Make sure to include relevant tags, emojis, and maintain the blog's style."


def generate_telegram_post_prompt(topic: str) -> str:
    prompt = f"Generate a post about {topic} for the Telegram channel. Include a catchy headline, a summary, and tags."
    return prompt


def summarize_channel_post_prompt(channel_name: str, topic: str) -> str:
    prompt = f"Summarize the main points made in {channel_name} about {topic}. Offer your opinion on the subject and include relevant hashtags."
    return prompt


def create_transition_post_prompt(topic: str, next_topic: str) -> str:
    prompt = f"Create a post about {topic} that seamlessly transitions into {next_topic}. Make sure to include relevant tags, emojis, and maintain the blog's style."
    return prompt


def mention_author_post_prompt(author_name: str, topic: str) -> str:
    prompt = f"Mention a recent post by {author_name} that is relevant to {topic}. Give your thoughts on it and tag the original author."
    return prompt


def summarize_article_prompt(content: str, previous: str) -> str:
    """Generate summary prompt"""
    prompt = f"""
    Briefly summarize the following problem step:

    '''
    {content}
    '''
    """

    if previous:
        prompt = (
            f"""
        Previous steps summary:
        {previous}
        """
            + prompt
            + " .Include your opinion and related tags."
        )

    return prompt
