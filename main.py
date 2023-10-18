#!/usr/bin/python3.11

from datetime import date, datetime, timedelta
from skcriteria.agg import simple
from skcriteria.preprocessing import invert_objectives

from modules import WebScraper

import json
import numpy as np
import os
import skcriteria as skc
import time

start = sorted(os.listdir('data'))[-1].split('.')[0]
start = datetime.strptime(start, '%Y-%m-%d') + timedelta(weeks=1)
start = start.date()

end = datetime.now().date()

while start <= end:
    if start.weekday() == 6:
        dt = start.strftime("%Y-%m-%d")
        ws = WebScraper(dt)
        with open(f'data/{dt}.json', 'w') as f:
            f.write(json.dumps(ws.parser()))
        time.sleep(1)
    start += timedelta(days=1)

listdir = sorted(os.listdir('data'))
counter = dict()

for name in listdir:
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
perf = []

for song, rank in zip(list(counter.keys()), rank.rank_):
    perf.append((song, int(np.int64(rank))))

data = sorted(perf, key=lambda x: x[1])
data = [{'title': eval(d[0])[0], 'artist': eval(d[0])[1], 'rank': d[1]} for d in data]

with open('export.json', 'w') as f:
    f.write(json.dumps({'data': data}))

with open('README.md', 'w') as f:
    end = listdir[-1].replace('.json', '')
    f.write('# GREATEST SONGS OF THE CENTURY\n\n')
    f.write(f'## Ranking [2000-01-02 - {end}]\n\n')
    f.write('| Title  | Artist | Rank |\n')
    f.write('| ------------- | ------------- | ------------- |\n')
    for d in data:
        f.write(f"| {' | '.join(map(str, d.values()))} |\n")
