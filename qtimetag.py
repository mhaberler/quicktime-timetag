#!/usr/bin/env python3
"""
time-tag a Quicktime MOV file

insert time-from-start in millisecond resolution and recording time

example: qtimetag.py --start 00:00:01 --end 00:00:2 /Users/mah/Downloads/IMG_3298.MOV
this will create /Users/mah/Downloads/IMG_3298_ts.MOV

pip install logzero ffmpeg-python  python-dateutil 
"""

import argparse
from logzero import logger
import ffmpeg
from dateutil import parser as dateparser
import os

ext = ".MOV"

def starttime(vfn: str):
    try:
        probe = ffmpeg.probe(vfn)
    except ffmpeg.Error as e:
        logger.error(e.stderr)
        return (None, None)

    video_stream = next(
        (stream for stream in probe["streams"]
         if stream["codec_type"] == "video"), None
    )
    if video_stream is None:
        logger.error(f"{vfn}: No video stream found")
        return (None, None)

    try:
        cd = video_stream["tags"]["creation_time"]
        start = dateparser.parse(cd)

        ts = int(round(start.timestamp()))
        logger.debug(f"created: {start=} {ts=}")
        return start, ts
    except Exception:
        logger.error(f"{vfn}: could not extract creation time")
        return (None, None)


def main(args):
    for fn in args.arg:
        recorded, ts = starttime(fn)
        path, filename = os.path.split(fn)
        if ts:  # IMG_329820231001_162959.MOV
            dest =  path + recorded.strftime("/%Y%m%d_%H%M%S_") + filename
        kwa = {}
        if args.start:
            kwa["ss"] = args.start
        if args.end:
            kwa["to"] = args.end
        in1 = ffmpeg.input(fn, **kwa)
        v1 = ffmpeg.drawtext(
            in1["v"],
            "%{pts:hms}\n\n " + recorded.strftime("%m/%d/%Y %H:%M:%S"),
            x=50,
            y="h-150",
            escape_text=False,
            box=1,
            boxborderw=15,
            boxcolor="black@0.7",
            fontsize=48,
            fontfile="/usr/share/fonts/truetype/arial.ttf",
            fontcolor="white",
        )
        a1 = in1["a"]
        joined = ffmpeg.concat(v1, a1, v=1, a=1)
        ffmpeg.output(joined, dest).overwrite_output().run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("arg", nargs="+", help=".MOV files to tag")
    parser.add_argument("-s", "--start", action="store",
                        dest="start", default=None)
    parser.add_argument("-e", "--end", action="store",
                        dest="end", default=None)

    args = parser.parse_args()
    main(args)
