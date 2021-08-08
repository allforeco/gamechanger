#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

if not sys.argv:
  sys.exit(1)

max_recs = 100000000000
try:
  max_recs = int(sys.argv[2])
except:
  pass
start_rec = 0

clicks = []
bad_clicks = 0
with open(sys.argv[1]) as f:
  for linenum, line in enumerate(f.readlines(),1):
    if linenum > max_recs:
      break
    try:
      clicks.append(pd.Timestamp(line))
    except:
      bad_clicks += 1


print(f"Parsed {len(clicks)} clicks, skipped {bad_clicks}, i.e. {100*bad_clicks/len(clicks)}%")

df = pd.DataFrame(
   {
       "Click time": clicks,
        "Click": [True]*len(clicks)
    }
)
df.groupby(pd.Grouper(key="Click time", freq='1W')).count().plot(kind='bar')
plt.show()

df = pd.DataFrame(
   {
       "Click time": [pd.Timestamp(click.strftime('2020-01-01 %X')) for click in clicks],
        "Click": [True]*len(clicks)
    }
)
df.groupby(pd.Grouper(key="Click time", freq='30Min')).count().plot(kind='bar')
plt.show()

