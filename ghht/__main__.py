from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime
from tempfile import mkstemp
import os.path

import fontTools.ttx
import numpy as np

import ghht


def parse_date(d):
    return datetime.datetime.strptime(d, "%Y-%m-%d")


def _main(sink, text, start_year, font_file, background, intensity, skip_list, debug):
    assert sink or debug, "sink or debug must be defined"
    ttx_file = mkstemp()[1] + ".ttx"
    print("converting font file '{:s}' to '{:s}'".format(font_file, ttx_file))
    fontTools.ttx.main(["-o", ttx_file, font_file])

    skip_dates = set()
    if skip_list:
        with open(skip_list) as f:
            skip_dates = set(parse_date(l.strip()) for l in f)
        print()
        print("skiplist contained {} dates to skip".format(len(skip_dates)))

    print()
    print("checking font has all chars in text '{}'".format(text))
    font = ghht.TTF(ttx_file)
    for ch in text:
        font.assert_has(ch)
        print("'{}' ok".format(ch))

    padding = ghht.Padding(top=1, right=1, left=1)

    def xy_dates():
        for (x, y), td in ghht.squares2commitdates(start_year, font.text2squares(text), padding):
            if td.date() in skip_dates:
                continue
            yield (x, y), td

    if debug:
        print("debug mode, will not generate commits")
        print("x y date")
        years = defaultdict(lambda: np.zeros(ghht.HeatMapCanvas.shape))
        for (x, y), td in xy_dates():
            print(x, y, td.date())
            years[td.date().year][y][x] += 1
        ghht.plot_debug_heatmap(sorted(years.items(), reverse=True))
        return

    if not os.path.isdir(os.path.join(sink, ".git")):
        print("'{}' does not have a .git directory, initializing repo".format(sink))
        ghht.run("git init", sink)

    print()
    print("generating commits")
    for (x, y), t in xy_dates():
        for _ in range(intensity):
            ghht.commit(t, sink, "({},{})".format(x, y))

    if background:
        print()
        print("generating commits for background")
        ghht.commit_year(start_year, sink)


def main():
    parser = ArgumentParser()
    parser.add_argument("text",
        type=str,
        help="ASCII text to render on commit heatmap.")
    parser.add_argument("start_year",
        type=int,
        help="Year for first commit.")
    parser.add_argument("--sink",
        type=str,
        help="Path to a git repository to be used for generating commits.")
    parser.add_argument("--font-file",
        type=str,
        default=ghht.DEFAULT_FONT,
        help="TTX-convertible font file.")
    parser.add_argument("--background",
        action="store_true",
        default=False,
        help="Generate a single commit on every day to paint a background.")
    parser.add_argument("--debug",
        action="store_true",
        default=False,
        help="Plot characters with matplotlib instead of generating commits.")
    parser.add_argument("--intensity",
        type=int,
        default=1,
        help="How many commits to generate for every text square.")
    parser.add_argument("--skip-list",
        type=str,
        help="Path to a file containing lines of yyyy-mm-dd for dates that should not have a commit.")

    _main(**vars(parser.parse_args()))


if __name__ == "__main__":
    main()
