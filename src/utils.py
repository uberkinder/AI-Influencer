import yaml
import openai
import os


def config(path: str = "config/config.yaml") -> dict:
    """
    Loads configurations from a YAML file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as config_file:
        return yaml.safe_load(config_file)


def load_secrets(env_path="config/.env"):
    """
    Loads secrets from .env and sets as environment variables.
    """
    # Check if .env exists
    if not os.path.exists(env_path):
        return

    # Load secrets from .env
    with open(env_path, "r") as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

    # Set OpenAI API key
    openai.api_key = os.environ["OPENAI_API_KEY"]
