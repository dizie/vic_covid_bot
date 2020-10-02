import glob
import os
from discord_bot import bot


def main():
    files = list(filter(os.path.isfile, glob.glob("*.jpg")))
    files.sort(key=lambda x: os.path.getctime(x))
    for file in files:
        bot("", "discord.json", file)


if __name__ == "__main__":
    main()
