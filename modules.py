from bs4 import BeautifulSoup
from typing import Dict, List, Union

import requests


class WebScraper:

    def __init__(self, date: str):
        self.date = date
        self.url = f'https://www.billboard.com/charts/hot-100/{self.date}/'

    def strips(self, s: str) -> str:
        """Remove \n and \t from string."""
        return s.replace('\t', '').replace('\n', '')

    def download(self) -> str:
        """Get HTML text."""
        try:
            resp = requests.get(self.url)
            return resp.text
        except Exception as e:
            return str(e)

    def parser(self) -> Dict[str, List[Union[str, int]]]:
        """Parse HTML and return HOT 100 songs."""
        soup = BeautifulSoup(self.download(), features='html.parser')
        rows = soup.select('div.o-chart-results-list-row-container')
        data = []

        for row in rows:
            song = []
            # 0 - current position
            # 1 - title
            # 2 - artist
            # 3 - last week
            # 4 - peak position
            # 5 - weeks on chart
            for i, j in enumerate(row.select('li')):
                if i == 4:
                    for sec in ('h3', 'span'):
                        song.append(self.strips(j.select(sec)[0].text))
                j = self.strips(j.text)
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

        return {self.date: data}
