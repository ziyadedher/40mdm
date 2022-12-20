from typing import Final, NewType, Optional

import dataclasses
import datetime
import os
import pathlib
import sys
import time
import urllib.request

import colorama
from loguru import logger

from mdm40 import openai_client, text_utils, imgtoansi

TITLE: Final[
    str
] = """
   ___ _____               _           
  /   |  _  |             | |           
 / /| | |/' |_ __ ___   __| |_ __ ___  
/ /_| |  /| | '_ ` _ \ / _` | '_ ` _ \ 
\___  \ |_/ / | | | | | (_| | | | | | |
    |_/\___/|_| |_| |_|\__,_|_| |_| |_|
"""

ROOT_FOLDER_PATH: pathlib.Path = pathlib.Path(__file__).absolute().parent.parent
ASSETS_FOLDER_NAME: Final[str] = "assets"
GAME_LOGS_FOLDER_NAME: Final[str] = "logs"


User = NewType("User", str)


@dataclasses.dataclass(frozen=True)
class Passcodes:
    active_passcodes: frozenset[str]
    expired_passcodes: frozenset[str]


def _wait_for_healthcheck() -> None:
    text_utils.type_with_delay(
        f"{colorama.Fore.LIGHTBLACK_EX}Getting you all set up! Give us a few seconds...{colorama.Fore.RESET}"
    )
    time.sleep(3)


def _get_passcodes(passcodes_file_path: pathlib.Path) -> Passcodes:
    active_passcodes: set[str] = set()
    expired_passcodes: set[str] = set()
    with open(passcodes_file_path, "r") as passcodes_file:
        for line in passcodes_file:
            passcode, raw_expired = line.split()
            is_expired = bool(int(raw_expired))
            if is_expired:
                expired_passcodes.add(passcode)
            else:
                active_passcodes.add(passcode)
    return Passcodes(frozenset(active_passcodes), frozenset(expired_passcodes))


def _authenticate_user(passcodes: Passcodes) -> Optional[User]:
    logger.info(f"Attempting to authenticate user...")

    given_passcode = text_utils.prompt(f"What is your passcode?")

    logger.debug(f"Got a passcode ({given_passcode}) from the user.")

    if given_passcode in passcodes.active_passcodes:
        user, _ = given_passcode.split("-")
        text_utils.type_with_delay(
            f"{colorama.Fore.LIGHTBLACK_EX}Passcode accepted, welcome {user}!{colorama.Fore.RESET}"
        )
        logger.info(f"Authenticated user ({user}) with passcode ({given_passcode}).")
        return User(user)
    elif given_passcode in passcodes.expired_passcodes:
        user, _ = given_passcode.split("-")
        text_utils.type_with_delay(
            f"{colorama.Fore.LIGHTBLACK_EX}Passcode is valid for {user}, but is expired. This is likely due to abuse. Please reach out to Ziyad if this is a mistake or you want a new passcode.{colorama.Fore.RESET}"
        )
        logger.info(
            f"Authenticated user ({user}) with passcode ({given_passcode}), but the passcode is expired."
        )
        return None
    else:
        text_utils.type_with_delay(
            f"{colorama.Fore.LIGHTBLACK_EX}Invalid passcode! Reach out to Ziyad if this is a mistake.{colorama.Fore.RESET}"
        )
        logger.info(
            f"Could not authenticate any user with the given passcode ({given_passcode})."
        )
        return None


def _greet_user(user: User) -> None:
    print(f"{colorama.Fore.RED}{TITLE}{colorama.Fore.RESET}")
    text_utils.type_with_delay(
        f"{colorama.Fore.RED}Welcome to 40mdm, {user}!{colorama.Fore.RESET}"
    )
    print()


def _setup_folders(
    root_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    assets_folder_path = root_path / ASSETS_FOLDER_NAME
    assets_folder_path.mkdir(exist_ok=True)

    logs_folder_path = root_path / GAME_LOGS_FOLDER_NAME
    logs_folder_path.mkdir(exist_ok=True)

    current_logs_folder_path = logs_folder_path / datetime.datetime.now().isoformat()
    current_logs_folder_path.mkdir(exist_ok=False)

    return assets_folder_path, logs_folder_path, current_logs_folder_path


def main() -> None:
    _wait_for_healthcheck()

    assets_folder_path, _, current_logs_folder_path = _setup_folders(ROOT_FOLDER_PATH)

    user = _authenticate_user(_get_passcodes(assets_folder_path / "passcodes.txt"))
    if user is None:
        exit(0)
    _greet_user(user)

    logger.debug("Setting up OpenAI client...")
    openai_client.setup_openai_client()
    logger.debug("Set up OpenAI client successfully.")

    logger.info(f"[{user}] Starting the game for user ({user})...")

    theme = text_utils.prompt("What would you like your story to be about?")
    logger.debug(f"[{user}] Gave an initial game prompt ({theme}).")

    text_utils.type_with_delay(
        f"{colorama.Fore.LIGHTBLACK_EX}Please wait while we generate your main character and story...{colorama.Fore.RESET}"
    )
    print()
    logger.debug(f"[{user}] Generating initial story...")

    story_theme = openai_client.complete_text(
        f"Vividly describe a theme for an amazing story heavily based and incorporating the following prompt:\n{theme}"
    )
    initial_prompt = "\n".join(
        [
            "You are a storyteller and game master setting the scene for a spectacular, fun, and engaging role-playing game.",
            "The stories you tell are captivating, funny, and beautiful."
            "Incorporate the following central theme in the game:",
            story_theme,
        ]
    )

    running_story = initial_prompt
    num_chapters = 0

    running_story += "\nWelcome the player and introduce the main character of the story with great enthusiasm, address the player directly in second person:\n"
    welcome = openai_client.complete_text(running_story, max_tokens=128)
    running_story += f"\n{welcome}"

    logger.debug(f"[{user}] Generated initial story successfully.")
    print(colorama.Fore.RED, end="")
    text_utils.type_with_delay(welcome)
    print(colorama.Fore.RESET, end="")
    print()

    text_utils.type_with_delay(
        f"{colorama.Fore.LIGHTBLACK_EX}Please wait while we generate your first chapter...{colorama.Fore.RESET}"
    )
    print()
    logger.debug(f"[{user}] Generating next scene...")

    running_story += "\nBased on the above, describe the intial scene of the story, address the player directly in second person:\n"
    new_story = openai_client.complete_text(running_story, max_tokens=128)
    running_story += f"\n{new_story}"

    chat_file_path = current_logs_folder_path / "chat.txt"

    while True:
        num_chapters += 1

        image_description = openai_client.complete_text(
            f"{running_story}\nDescribe objectively, in third-person, what the user sees right now:\n",
            max_tokens=128,
        )
        image_file_path = current_logs_folder_path / f"{num_chapters:03d}.png"
        urllib.request.urlretrieve(
            openai_client.generate_image(image_description),
            filename=str(image_file_path),
        )
        image_ansi = imgtoansi.convert(image_file_path)
        print(image_ansi)

        running_story += "\nBased on the story above, briefly describe a 3 short options the user can take. Format the options as numbered bullet points in short imperative-tense sentences:\n"
        new_options = openai_client.complete_text(running_story)
        running_story += f"\n{new_options}"

        logger.debug(f"[{user}] Generated next scene.")
        print(colorama.Fore.RED, end="")
        text_utils.type_with_delay(new_story)
        print(colorama.Fore.RESET, end="")
        print()

        print(colorama.Fore.BLUE, end="")
        text_utils.type_with_delay(
            "Here are suggested actions, but you can type whatever you want to do:"
        )
        text_utils.type_with_delay(new_options)
        print()
        user_action = text_utils.prompt()
        logger.debug(f"[{user}] User inputted action ({user_action}).")

        text_utils.type_with_delay(
            f"{colorama.Fore.LIGHTBLACK_EX}Please wait while we generate the next chapter...{colorama.Fore.RESET}"
        )
        print()
        logger.debug(f"[{user}] Generating next scene...")

        running_story += f"\nThe user takes the following action: {user_action}\n"

        running_story += "\nBased on the above story, theme, and actions that the user has taken, continue the story:\n"
        new_story = openai_client.complete_text(running_story).strip()
        running_story += f"\n{new_story}"

        with open(chat_file_path, "w") as chat_file:
            chat_file.write(running_story)


if __name__ == "__main__":
    colorama.init(strip=False)

    try:
        main()
    except KeyboardInterrupt:
        print(colorama.Fore.LIGHTBLACK_EX, end="")
        text_utils.type_with_delay("Goodbye, adventurer!", delay=10)
        print(colorama.Fore.RESET, end="")
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
