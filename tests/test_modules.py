from modules import WebScraper


def test_web_scraper():
    ws = WebScraper('2009-01-01')
    assert len(list(ws.parser().values())[0]) == 100
