import aiofiles
import json
import os
import typing as t

from aiohttp import ClientSession
from asyncio import Semaphore
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio

from const import DIRECTORY

from utils import get_billboard_chart_data
from utils import get_missing_weekly_dates


async def worker(date: str, session: ClientSession, semaphore: Semaphore) -> None:
    """
    Fetch and save the Billboard Hot 100 chart data for a given date.

    Parameters
    ----------
    date (str)
        The date in the format YYYY-MM-DD for which to fetch the chart data.

    session (ClientSession)
        The aiohttp ClientSession object for making requests.

    semaphore (Semaphore)
        A semaphore object for rate-limiting requests.

    Returns
    -------
    None
    """
    async with semaphore:
        async with session.get(f"https://www.billboard.com/charts/hot-100/{date}/") as resp:
            markup = await resp.text()
            if (data := get_billboard_chart_data(markup)):
                async with aiofiles.open(DIRECTORY / f"{date}.json", "w") as f:
                    await f.write(json.dumps({date: data}))


async def scraper(start_date: datetime) -> None:
    """
    Scrape the Billboard Hot 100 chart data for missing dates.

    Parameters
    ----------
    start_date (datetime)
        The start date from which to check for missing chart data.

    Returns
    -------
    None
    """
    if (dates := get_missing_weekly_dates(start_date, DIRECTORY)):
        semaphore = Semaphore(5)
        async with ClientSession() as session:
            tasks = [worker(date, session, semaphore) for date in dates]
            await tqdm_asyncio.gather(*tasks)


def ranking() -> t.List[t.Tuple[str, str, int]]:
    """
    Compute the ranking of songs based on their peak position and number of weeks on the Billboard Hot 100 chart.

    Parameters
    ----------
    None

    Returns
    -------
    List[Tuple[str, str, int]]
        A list of tuples, which represents a song with its title, artist, and rank.
    """
    collation = {}
    for filename in os.listdir(DIRECTORY):
        with open(DIRECTORY / filename, "r") as f:
            data = json.load(f)
        entries = list(data.values())[0]
        for entry in entries:
            position = entry[0]
            title = entry[1]
            artist = entry[2]
            if not collation.get((title, artist)):
                collation[(title, artist)] = []
            collation[(title, artist)].append(position)

    metrics = {}
    for song, positions in collation.items():
        points = sum(101 - position for position in positions)
        metrics[song] = points
    metrics = sorted(metrics.items(), key=lambda item: item[1], reverse=True)

    output = []
    current_rank = 1
    for i, (song, points) in enumerate(metrics):
        if i > 0 and points < metrics[i-1][1]:
            current_rank = i + 1
        output.append((song[0], song[1], current_rank))

    return output
