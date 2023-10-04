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

# start date must be after 2023-09-17
start, end = date(2023, 9, 18), datetime.now().date()

while start <= end:
    if start.weekday() == 6:
        dt = start.strftime("%Y-%m-%d")
        ws = WebScraper(dt)
        with open(f'data/{dt}.json', 'w') as f:
            f.write(json.dumps(ws.parser()))
        time.sleep(1)
    start += timedelta(days=1)

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
perf = []

for song, rank in zip(list(counter.keys()), rank.rank_):
    perf.append((song, int(np.int64(rank))))

data = sorted(perf, key=lambda x: x[1])

with open('export.json', 'w') as f:
    f.write(json.dumps({"data": data}))

with open('README.md', 'w') as f:
    end = sorted(os.listdir('data'))[-1].replace('.json', '')
    f.write('# GREATEST SONGS OF THE CENTURY\n\n')
    f.write(f'## Ranking [2000-01-02 - {end}]\n\n')
    f.write('| Title  | Artist | Rank |\n')
    f.write('| ------------- | ------------- | ------------- |\n')
    for d in data:
        f.write(f"| {' | '.join([*eval(d[0]), str(d[1])])} |\n")
