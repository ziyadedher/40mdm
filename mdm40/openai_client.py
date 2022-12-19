from typing import Final

import os

import openai
from loguru import logger


OPENAI_API_KEY_ENV_VAR_NAME: Final[str] = "OPENAI_API_KEY"


def setup_openai_client() -> None:
    openai_api_key = os.getenv(OPENAI_API_KEY_ENV_VAR_NAME)
    if openai_api_key is None:
        logger.error(
            f"Could not get OpenAI API key from environment variable {OPENAI_API_KEY_ENV_VAR_NAME}, exiting..."
        )
        exit(1)
    openai.api_key = openai_api_key


def complete_text(prompt: str, *, max_tokens: int = 256) -> str:
    return openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.5,
    )["choices"][0]["text"].strip()


def generate_image(prompt: str) -> str:
    return openai.Image.create(prompt=prompt, n=1, size="256x256")["data"][0]["url"]
