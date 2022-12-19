import statistics
import time
import sys

import colorama


def type_with_delay(
    string: str, *, delay: float = 20, spread: float = 0.25, final_newline: bool = True
) -> None:
    new_string = ""
    counter = 0
    for c in string:
        new_string += c
        counter += 1
        if c == "\n":
            counter = 0
        elif counter == 95:
            new_string += "\n"
            counter = 0
    string = new_string

    dist = statistics.NormalDist(delay, delay * spread)

    for k, semistring in enumerate(string.split("\n")):
        for i, _ in enumerate(semistring):
            substr = semistring[: i + 1]
            print("\r" + substr, end="")
            sys.stdout.flush()
            time.sleep(max(0, dist.samples(1)[0] / 1e3))
        if k != string.count("\n") or final_newline:
            print()


def prompt(prompt: str = "What do you do?") -> str:
    print(colorama.Fore.BLUE, end="")
    type_with_delay(prompt + "\n> ", final_newline=False)
    try:
        inp = input()
    except EOFError:
        exit(0)
    print(colorama.Fore.RESET, end="")
    return str(inp)
