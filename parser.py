from bs4 import BeautifulSoup

import requests
import typing as t


class Parser:
    def __init__(self, url: str):
        self.url = url

    def get(self) -> str:
        r = requests.get(self.url)
        if r.status_code == 200:
            return r.text
        return ''

    @staticmethod
    def parse(markup: str) -> t.List[t.Dict[str, str]]:
        data = []
        soup = BeautifulSoup(markup, features='html.parser')
        divs = soup.select('div.o-chart-results-list-row-container')
        for div in divs:
            row = div.select_one('h3#title-of-a-story')
            data.append({
                "title": row.text.strip(),
                "artist": list(row.next_siblings)[1].text.strip()
            })
        return data
