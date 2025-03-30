from aiohttp import ClientSession
from asyncio import Semaphore
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from tqdm.asyncio import tqdm_asyncio

import asyncio
import typing as t
import unisql
import unisql.asyncio


def ranking():
    db = unisql.connect.sqlite('data.db')

    query = 'SELECT MIN(date) AS date FROM chart;'
    fetch = db.fetch(query, multiple=False)
    start_date = fetch['date']

    query = 'SELECT MAX(date) AS date FROM chart;'
    fetch = db.fetch(query, multiple=False)
    end_date = fetch['date']

    query = """
        WITH RankedSongs AS (
            SELECT 
                title,
                artist,
                MIN(date) AS entry,
                SUM(101 - position) AS score
            FROM chart
            GROUP BY title, artist
        )
        SELECT 
            DENSE_RANK() OVER (ORDER BY score DESC) AS rank,
            title,
            artist,
            entry,
            score
        FROM RankedSongs
        ORDER BY rank;
    """
    songs = [list(song.values()) for song in db.fetch(query)]

    with open('README.md', 'w') as f:
        f.write("# Billboard's Historical Ranking\n\n")
        f.write(f'## Ranking [{start_date} - {end_date}]\n\n')
        f.write('| Rank  | Title | Artist | Entry | Score |\n')
        f.write(f'{"| ------------- "*5}|\n')

        for song in songs:
            f.write(f'| {" | ".join(map(str, song))} |\n')

    db.close()


def htmlparser(markup: str) -> t.List[t.List[t.Any]]:
    """
    Extracts song information from a Billboard chart HTML markup.

    Parameters
    ----------
    markup (str)
        The HTML markup containing the Billboard chart data.

    Returns
    -------
    List[List[Any]]
        A list of lists containing song information. Each sublist represents a song and contains the following data:
            - Current position (int)
            - Title (str)
            - Artist (str)
            - Last week's position (int)
            - Peak position (int)
            - Weeks on chart (int)

    Examples
    --------
    >>> markup = '<div class='o-chart-results-list-row-container'>...</div>'
    >>> data = htmlparser(markup)
    >>> data[0]
    [1, 'Watermelon Sugar', 'Harry Styles', 3, 1, 20]
    """

    def nowhitespace(k): return k.replace('\t', '').replace('\n', '')

    data = []

    soup = BeautifulSoup(markup, features='html.parser')
    rows = soup.select('div.o-chart-results-list-row-container')

    for row in rows:
        song = []
        for i, j in enumerate(row.select('li')):
            if i == 4:
                for sec in ('h3', 'span'):
                    song.append(nowhitespace(j.select(sec)[0].text))
            else:
                j = nowhitespace(j.text)
                match i:
                    case 0:
                        j = j.replace('NEW', '').replace('RE-ENTRY', '')
                        song.append(int(j))
                    case 13:
                        song.append(0 if j == '-' else int(j))
                    case 14:
                        song.append(int(j))
                    case 15:
                        song.append(int(j))
        data.append(song)

    return data


async def worker(date: str, db: unisql.asyncio.connect, session: ClientSession, semaphore: Semaphore) -> None:
    async with semaphore:
        async with session.get(f'https://www.billboard.com/charts/hot-100/{date}/') as r:
            if (data := htmlparser(await r.text())):
                query = 'INSERT INTO chart(date, title, artist, position) VALUES(?, ?, ?, ?);'
                value = [(date, d[1], d[2], d[0]) for d in data]
                await db.execute(query, value)


async def update(start_datetime: datetime) -> None:
    db = await unisql.asyncio.connect.sqlite('data.db')

    query = 'SELECT MAX(date) AS latest FROM chart;'
    fetch = await db.fetch(query, multiple=False)

    if (latest := fetch['latest']):
        start_datetime = datetime.strptime(latest, '%Y-%m-%d') + timedelta(weeks=1)

    dates = []

    while start_datetime <= datetime.now():
        dates.append(start_datetime.strftime('%Y-%m-%d'))
        start_datetime += timedelta(weeks=1)

    semaphore = Semaphore(5)

    async with ClientSession() as session:
        await tqdm_asyncio.gather(*[worker(date, db, session, semaphore) for date in dates])

    await db.close()

    ranking()


if __name__ == '__main__':
    asyncio.run(update(datetime(2000, 1, 2)))
