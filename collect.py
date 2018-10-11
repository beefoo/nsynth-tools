# -*- coding: utf-8 -*-

# Collect all:
    # python collect.py
# Collect just synthetic instruments sorted by pitch and grouped by instrument family:
    # python collect.py -filter "instrument_source_str=acoustic" -sort "pitch=desc,instrument_family_str=asc" -overlap 100
    # python collect.py -filter "instrument_family_str=guitar,instrument_source_str=acoustic" -sort "pitch=desc,instrument_str=asc" -overlap 100

import argparse
import json
import math
import os
import numpy as np
from pydub import AudioSegment
from pprint import pprint
import sys
import time

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_JSON", default="downloads/nsynth-test/examples.json", help="Input JSON file")
parser.add_argument('-audio', dest="INPUT_AUDIO", default="downloads/nsynth-test/audio/%s.wav", help="Input audio file pattern")
parser.add_argument('-filter', dest="FILTER", default="", help="Comma-separated pairs, e.g. instrument_family_str=bass,instrument_source_str=synthetic")
parser.add_argument('-sort', dest="SORT_BY", default="", help="Comma-separated pairs, e.g. pitch=desc,instrument_family_str=asc")
parser.add_argument('-max', dest="MAX_DURATION", default=6000, type=int, help="Max duration in seconds")
parser.add_argument('-cstart', dest="CLIP_START", default=0, type=int, help="Clip start in milliseconds")
parser.add_argument('-cdur', dest="CLIP_DUR", default=250, type=int, help="Clip duration in milliseconds")
parser.add_argument('-fadein', dest="FADE_IN", default=10, type=int, help="Amount to fade in in milliseconds")
parser.add_argument('-fadeout', dest="FADE_OUT", default=125, type=int, help="Amount to fade out in milliseconds")
parser.add_argument('-overlap', dest="OVERLAP", default=0, type=int, help="Amount to overlap in milliseconds")
parser.add_argument('-pstart', dest="PAD_START", default=200, type=int, help="Amount to pad start in milliseconds")
parser.add_argument('-pend', dest="PAD_END", default=200, type=int, help="Amount to pad end in milliseconds")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/examples.mp3", help="Input audio file")
parser.add_argument('-manifest', dest="MANIFEST_FILE", default="output/examples.json", help="Output manifest file")
args = parser.parse_args()

# Parse arguments
INPUT_JSON = args.INPUT_JSON
INPUT_AUDIO = args.INPUT_AUDIO
FILTERS = [] if len(args.FILTER) <= 0 else [tuple(f.split("=")) for f in args.FILTER.split(",")]
SORTERS = [] if len(args.SORT_BY) <= 0 else [tuple(f.split("=")) for f in args.SORT_BY.split(",")]
MAX_DURATION = args.MAX_DURATION * 1000
CLIP_START = args.CLIP_START
CLIP_DUR = args.CLIP_DUR
FADE_IN = args.FADE_IN
FADE_OUT = args.FADE_OUT
OVERLAP = args.OVERLAP
PAD_START = args.PAD_START
PAD_END = args.PAD_END
OUTPUT_FILE = args.OUTPUT_FILE
MANIFEST_FILE = args.MANIFEST_FILE

# Audio config
FRAME_RATE = 44100
SAMPLE_WIDTH = 2
CHANNELS = 2

print("Reading %s..." % INPUT_JSON)
dataIn = {}
with open(INPUT_JSON) as f:
    dataIn = json.load(f)
files = list(dataIn.keys())
print("Loaded %s with %s entries" % (INPUT_JSON, len(files)))

# Make a list of dicts, sorted by name
files.sort()
files = [dataIn[f] for f in files]

# Filter results
for key, value in FILTERS:
    files = [f for f in files if str(f[key])==str(value)]

# Sort results
for key, direction in SORTERS:
    reversed = (direction == "desc")
    files = sorted(files, key=lambda k: k[key], reverse=reversed)

fileCount = len(files)
if len(FILTERS) > 0:
    print("Found %s files after filtering." % fileCount)

if fileCount <= 0:
    sys.exit()

duration = fileCount * CLIP_DUR - (fileCount-1) * OVERLAP
print("Total time: %s" % time.strftime('%H:%M:%S', time.gmtime(duration/1000)))

# Too long
if duration > MAX_DURATION:
    targetClipCount = 1.0 * (MAX_DURATION - OVERLAP) / (CLIP_DUR - OVERLAP)
    targetClipCount = int(math.floor(targetClipCount))
    print("Duration is too long. Trimming to %s clips" % targetClipCount)
    files = files[:targetClipCount]
    fileCount = len(files)
    duration = fileCount * CLIP_DUR - (fileCount-1) * OVERLAP
    print("New total time: %s" % time.strftime('%H:%M:%S', time.gmtime(duration/1000)))

# Add padding
duration += PAD_START + PAD_END

# Start building the audio
baseAudio = AudioSegment.silent(duration=duration, frame_rate=FRAME_RATE)
baseAudio = baseAudio.set_channels(CHANNELS)
baseAudio = baseAudio.set_sample_width(SAMPLE_WIDTH)

print("Building audio...")
ms = PAD_START
manifest = {}
for i, f in enumerate(files):
    filename = INPUT_AUDIO % f["note_str"]
    fformat = filename.split(".")[-1].lower()
    audio = AudioSegment.from_file(filename, format=fformat)

    # convert to stereo
    if audio.channels != CHANNELS:
        audio = audio.set_channels(CHANNELS)
    # convert sample width
    if audio.sample_width != SAMPLE_WIDTH:
        audio = audio.set_sample_width(SAMPLE_WIDTH)
    # convert sample rate
    if audio.frame_rate != FRAME_RATE:
        audio = audio.set_frame_rate(FRAME_RATE)

    audioDur = len(audio)
    # clip audio
    clipEnd = min(CLIP_START + CLIP_DUR, audioDur)
    clip = audio[CLIP_START:clipEnd]
    clipDur = len(clip)
    # add fade
    clip = clip.fade_in(min(clipDur, FADE_IN)).fade_out(min(clipDur, FADE_OUT))
    baseAudio = baseAudio.overlay(clip, position=ms)

    # add to manifest
    manifest[f["note_str"]] = [ms, clipDur]
    overlap = min(OVERLAP, clipDur/2)
    ms += (clipDur - overlap)

    # progress
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*(i+1)/fileCount*100,1))
    sys.stdout.flush()


print("Writing to file...")
format = OUTPUT_FILE.split(".")[-1]
baseAudio.export(OUTPUT_FILE, format=format)
print("Wrote to %s" % OUTPUT_FILE)

if len(MANIFEST_FILE) > 0:
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f)
        print("Wrote to %s" % MANIFEST_FILE)
