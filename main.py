import sys
import typing as t
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable, TableStyle
from sqlite7 import connect

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB_PATH = "data.db"
OUTPUT_FILE = "README.md"
TOP_N = 500  # rank-based limit

# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_chart(html: str) -> t.List[t.Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("div.o-chart-results-list-row-container")

    out = []
    for r in rows:
        title = r.select_one("h3#title-of-a-story")
        if not title:
            continue

        sib = list(title.next_siblings)
        if len(sib) < 2:
            continue

        out.append({
            "title": title.text.strip(),
            "artist": sib[1].text.strip()
        })

    return out


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

def scrape():
    session = requests.Session()

    with connect(DB_PATH) as db:
        table = db.table("chart")

        last = table.select(columns=["date"], order_by="date desc", limit=1)[0]["date"]

        current = datetime.strptime(last, "%Y-%m-%d") + timedelta(days=7)

        # Billboard prevents the retrieval of past week’s data.
        # Otherwise, we have to rely on the Wayback Machine to retrieve past data.

        res = session.get("https://www.billboard.com/charts/hot-100/", timeout=60)
        entries = parse_chart(res.text)

        rows = [
            {
                "date": current.strftime("%Y-%m-%d"),
                "title": e["title"],
                "artist": e["artist"],
                "position": idx + 1
            }
            for idx, e in enumerate(entries)
        ]

        table.insert_many(rows=rows, on_conflict="ignore")

        print(f"{current.date()} → {len(rows)} saved")


# ---------------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------------
QUERY = """
WITH ranked AS (
    SELECT
        title,
        artist,
        MIN(date) AS first_entry_date,
        SUM(101 - position) AS score
    FROM chart
    GROUP BY title, artist
),
final AS (
    SELECT
        DENSE_RANK() OVER (ORDER BY score DESC) AS rank,
        title,
        artist,
        first_entry_date,
        score
    FROM ranked
)
SELECT *
FROM final
WHERE rank <= {}
ORDER BY rank;
"""


def generate_report():
    with connect(DB_PATH) as db:
        start = db.fetch_one("SELECT MIN(date) AS d FROM chart;")["d"]
        end = db.fetch_one("SELECT MAX(date) AS d FROM chart;")["d"]

        rows = db.fetch_all(QUERY.format(TOP_N))
        data = [list(r.values()) for r in rows]

    table = PrettyTable()
    table.field_names = ["Rank", "Title", "Artist", "Entry", "Score"]
    table.add_rows(data)
    table.set_style(TableStyle.MARKDOWN)

    content = "\n".join([
        "# Billboard's Historical Ranking\n",
        f"## Top {TOP_N} [{start} - {end}]\n",
        str(table)
    ])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Report generated → {OUTPUT_FILE}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n🎵 Billboard Scraper\n")

    scrape()
    generate_report()

    print("\n✅ Pipeline complete\n")


if __name__ == "__main__":
    main()
