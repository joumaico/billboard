import os
import pathlib
import typing as t

from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta


def get_billboard_chart_data(markup: str) -> t.List[t.List[t.Any]]:
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
    >>> markup = '<div class="o-chart-results-list-row-container">...</div>'
    >>> data = get_billboard_chart_data(markup)
    >>> data[0]
    [1, "Watermelon Sugar", "Harry Styles", 3, 1, 20]
    """
    data = []
    soup = BeautifulSoup(markup, features="html.parser")
    rows = soup.select("div.o-chart-results-list-row-container")

    for row in rows:
        song = []
        for i, j in enumerate(row.select("li")):
            if i == 4:
                for sec in ("h3", "span"):
                    song.append(remove_whitespace(j.select(sec)[0].text))
            else:
                j = remove_whitespace(j.text)
                match i:
                    case 0:
                        j = j.replace("NEW", "").replace("RE-ENTRY", "")
                        song.append(int(j))
                    case 13:
                        song.append(0 if j == "-" else int(j))
                    case 14:
                        song.append(int(j))
                    case 15:
                        song.append(int(j))
        data.append(song)

    return data


def get_missing_weekly_dates(start_date: datetime, directory: pathlib.Path) -> t.Set[str]:
    """
    Get a set of missing weekly dates from a given start date to the current date.

    Parameters
    ----------
    start_date (datetime)
        The start date from which to generate weekly dates.

    directory (pathlib.Path)
        The directory path to check for existing dates.

    Returns
    -------
    Set[str]
        A set of missing weekly dates in string format.
    """
    start_date = start_date.date()
    end_date = datetime.now().date()

    dates = set()

    while start_date < end_date:
        dates.add(str(start_date))
        start_date += timedelta(weeks=1)

    exists = set(pathlib.Path(p).stem for p in os.listdir(directory))

    return dates - exists


def remove_whitespace(string: str) -> str:
    """
    Remove whitespace characters (tabs and newlines) from a given string.

    Parameters
    ----------
    string (str)
        The input string from which to remove whitespace characters.

    Returns
    -------
    str
        A new string with all tab and newline characters removed.
    """
    return string.replace("\t", "").replace("\n", "")
