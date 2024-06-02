import asyncio
import os
import pathlib
import zipfile

from const import DIRECTORY
from const import START_DATE

from modules import ranking
from modules import scraper


def main():
    if not os.path.exists(DIRECTORY):
        os.mkdir(DIRECTORY)

    if not os.listdir(DIRECTORY):
        with zipfile.ZipFile("shared/data.zip", "r") as ref:
            ref.extractall(DIRECTORY)

    asyncio.run(scraper(START_DATE))

    with open("README.md", "w") as f:
        files = sorted(os.listdir(DIRECTORY))

        f.write("# Billboard's Historical Ranking\n\n")
        f.write(f"## Ranking [{pathlib.Path(files[0]).stem} - {pathlib.Path(files[-1]).stem}]\n\n")
        f.write("| Title  | Artist | Rank |\n")
        f.write("| ------------- | ------------- | ------------- |\n")

        for item in ranking():
            f.write(f"| {' | '.join(map(str, item))} |\n")


if __name__ == "__main__":
    main()
