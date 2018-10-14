# -*- coding: utf-8 -*-

# View all:
    # python stats.py -in downloads/nsynth-train/examples.json
# Sample queries:
    # python stats.py -filter "instrument_family_str=bass&instrument_source_str=synthetic"
    # python stats.py -in downloads/nsynth-train/examples.json -filter "instrument_family_str=mallet&instrument_source_str=acoustic&pitch=<60&pitch=>40&velocity=<75"

import argparse
import collections
import json
from lib import *
import math
from matplotlib import pyplot as plt
import os
import numpy as np
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_JSON", default="downloads/nsynth-test/examples.json", help="Input JSON file")
parser.add_argument('-filter', dest="FILTER", default="", help="Comma-separted pairs, e.g. instrument_family_str=bass&instrument_source_str=synthetic")
args = parser.parse_args()

# Parse arguments
INPUT_JSON = args.INPUT_JSON
FILTERS = [] if len(args.FILTER) <= 0 else [tuple(f.split("=")) for f in args.FILTER.split("&")]

PLOT_SIZE = (24, 8)
ROWS = 2
MAX_LABELS = 12

print("Reading %s..." % INPUT_JSON)
dataIn = {}
with open(INPUT_JSON) as f:
    dataIn = json.load(f)
files = list(dataIn.keys())
print("Loaded %s with %s entries" % (INPUT_JSON, len(files)))

# Make a list of dicts, sorted by name
files.sort()
files = [dataIn[f] for f in files]
# pprint(files[:3])

files = filterResults(files, FILTERS)

fileCount = len(files)
if len(FILTERS) > 0:
    print("Found %s files after filtering." % fileCount)

if fileCount <= 0:
    sys.exit()

instruments = list(set([f["instrument_str"] for f in files]))
print("%s unique instruments found." % len(instruments))

dataKeys = [
    ("instrument_family_str", "Family"),
    ("instrument_source_str", "Source"),
    ("pitch", "Pitch"),
    ("qualities_str", "Quality"),
    ("velocity", "Velocity"),
    ("instrument", "Unique instrument")
]
keyCount = len(dataKeys)
COLS = int(math.ceil(1.0 * keyCount / ROWS))

plt.figure(figsize=PLOT_SIZE)
for i, pair in enumerate(dataKeys):
    key, label = pair
    isList = isinstance(files[0][key], (list,))
    if isList:
        values = []
        for f in files:
            values += f[key]
        values = [str(v) for v in values]
    else:
        values = [str(f[key]) for f in files]
    counter = collections.Counter(values)
    counted = counter.most_common()

    ys = [c[1] for c in counted]
    xs = np.arange(len(ys))

    # set subplot
    ax = plt.subplot(ROWS, COLS, i+1)
    ax.set_title(label)

    # too many values, just plot it
    if len(xs) > MAX_LABELS:
        ys = [f[key] for f in files]
        plt.hist(ys, bins=50)

    # otherwise, show bargraph
    else:
        xLabels = [c[0] for c in counted]
        for i, y in enumerate(ys):
            ax.text(xs[i], y * 0.5, str(y), va="center", ha="center")
        plt.xticks(xs, tuple(xLabels), rotation=45)
        plt.bar(xs, ys)
plt.tight_layout()
plt.show()
