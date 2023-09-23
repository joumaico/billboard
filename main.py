#!/usr/bin/python3.11

from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from skcriteria.agg import simple
from skcriteria.preprocessing import invert_objectives

import json
import numpy as np
import os
import pathlib
import requests
import shutil
import skcriteria as skc
import time


def strips(s: str) -> str:
    #  remove \n and \t
    return s.replace('\t', '').replace('\n', '')


def parser(fp: str) -> dict:
    # parse information from raw html file
    with open(fp, 'r') as f:
        html = f.read()

    soup = BeautifulSoup(html, features='html.parser')
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
                    song.append(strips(j.select(sec)[0].text))
            text = strips(j.text)
            match i:
                case 0:
                    text = text.replace('NEW', '').replace('RE-ENTRY', '')
                    song.append(int(text))
                case 13:
                    song.append(0 if text == '-' else int(text))
                case 14:
                    song.append(int(text))
                case 15:
                    song.append(int(text))
        data.append(song)

    return {pathlib.Path(fp).stem: data}


# make a folders to store html and json files
for folder in ('.tmp', 'data'):
    if not os.path.exists(folder):
        os.mkdir(folder)

# start date must be after 2023-09-17
start, end = date(2023, 9, 18), datetime.now().date()

while start <= end:
    if start.weekday() == 6:
        dt = start.strftime("%Y-%m-%d")
        url = f'https://www.billboard.com/charts/hot-100/{dt}/'
        resp = requests.get(url)
        with open(f'.tmp/{dt}.html', 'w') as f:
            f.write(resp.text)
        time.sleep(2)
    start += timedelta(days=1)

for name in sorted(os.listdir('.tmp')):
    path = f'.tmp/{name}'
    with open(f'data/{pathlib.Path(path).stem}.json', 'w') as f:
        f.write(json.dumps(parser(path)))

counter = dict()

for name in sorted(os.listdir('data')):
    with open(f'data/{name}', 'r') as f:
        d = json.loads(f.read())
    items = list(d.values())[0]
    for item in items:
        # {(title, artist): (peak, weeks)}
        counter[str((item[1], item[2]))] = [item[4], item[5]]

matrix = list(counter.values())
dm = skc.mkdm(matrix, [min, max])
inverter = invert_objectives.InvertMinimize()

dmt = inverter.transform(dm)
dec = simple.WeightedSumModel()

rank = dec.evaluate(dmt)
performance = []

for song, rank in zip(list(counter.keys()), rank.rank_):
    performance.append((song, int(np.int64(rank))))

data = sorted(performance, key=lambda x: x[1])

with open('README.md', 'w') as f:
    end = sorted(os.listdir('data'))[-1].replace('.json', '')
    f.write('# GREATEST SONGS OF THE CENTURY\n\n')
    f.write('## Source Data\n\n')
    f.write('**[↓ Billboard+Hot+100.2000_01_02-2023_09_17.raw.tar.gz](https://s3.ap-southeast-1.amazonaws.com/static.joumaico.me/Billboard+Hot+100.2000_01_02-2023_09_17.raw.tar.gz)**\n\n')
    f.write(f'## Ranking [2000-01-02 - {end}]\n\n')
    f.write('| Title  | Artist | Rank |\n')
    f.write('| ------------- | ------------- | ------------- |\n')
    for d in data:
        f.write(f"| {' | '.join([*eval(d[0]), str(d[1])])} |\n")

# get the top 2% performing songs
analyze = dict(data[:int(len(data) * 0.02)])
maximum = list(analyze.items())[-1][1]

# include the overflowed item
for d in data:
    if d[1] > maximum:
        break
    if d[0] not in analyze:
        analyze[d[0]] = d[1]

with open('analyze.json', 'w') as f:
    f.write(json.dumps(analyze))

shutil.rmtree('.tmp')
