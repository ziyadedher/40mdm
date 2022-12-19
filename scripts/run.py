from typing import Final

import datetime
import pathlib
import socket
import urllib.request

import colorama

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

IMAGES_FOLDER: pathlib.Path = pathlib.Path(__file__).absolute().parent / "images"


def main() -> None:
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.bind(("localhost", "8888"))
    # s.accept()

    print(f"{colorama.Fore.RED}{TITLE}{colorama.Fore.RESET}")
    text_utils.type_with_delay(
        f"{colorama.Fore.RED}Welcome to 40mdm!{colorama.Fore.RESET}"
    )
    print()

    IMAGES_FOLDER.mkdir(exist_ok=True)
    current_folder = IMAGES_FOLDER / datetime.datetime.now().isoformat()
    current_folder.mkdir(exist_ok=False)

    openai_client.setup_openai_client()

    theme = text_utils.prompt(prompt="What would you like your story to be about?\n> ")
    print()

    text_utils.type_with_delay(
        f"{colorama.Fore.LIGHTBLACK_EX}Please wait while we generate a story for you...{colorama.Fore.RESET}"
    )
    print()

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
    print(colorama.Fore.RED, end="")
    text_utils.type_with_delay(welcome)
    print(colorama.Fore.RESET, end="")
    print()

    running_story += "\nBased on the above, describe the intial scene of the story, address the player directly in second person:\n"
    new_story = openai_client.complete_text(running_story, max_tokens=128)
    running_story += f"\n{new_story}"

    chat_file_path = current_folder / "chat.txt"

    while True:
        num_chapters += 1

        image_description = openai_client.complete_text(
            f"{running_story}\nDescribe objectively, in third-person, what the user sees right now:\n",
            max_tokens=128,
        )
        image_file_path = current_folder / f"{num_chapters:03d}.png"
        urllib.request.urlretrieve(
            openai_client.generate_image(image_description),
            filename=str(image_file_path),
        )
        image_ansi = imgtoansi.convert(image_file_path)
        print(image_ansi)

        # inventory = openai_client.complete_text(
        #     f"{running_story}\nList all the items currently in the user's inventory as a bullet point list:\n"
        # )
        # print(inventory)

        running_story += "\nBased on the story above, briefly describe a few short options the user can take. Format the options as numbered bullet points in short imperative-tense sentences:\n"
        new_options = openai_client.complete_text(running_story)
        running_story += f"\n{new_options}"

        print(colorama.Fore.RED, end="")
        text_utils.type_with_delay(new_story)
        print(colorama.Fore.RESET, end="")
        print()

        print(colorama.Fore.BLUE, end="")
        text_utils.type_with_delay("Here are some things you could do:")
        text_utils.type_with_delay(new_options)
        print()
        user_action = text_utils.prompt()

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
        print(colorama.Fore.LIGHTBLACK_EX)
        text_utils.type_with_delay("Goodbye, adventurer!", delay=10)
        print(colorama.Fore.RESET)
