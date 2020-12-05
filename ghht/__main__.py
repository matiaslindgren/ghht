import argparse
import datetime
import string
import tempfile

import fontTools.ttx
import ghht


def parse_date(d):
    return datetime.datetime.strptime(d, "%Y-%m-%d")


def _main(sink_repo, text, start_date, font_file, background, intensity, skip_list):
    ttx_file = tempfile.mkstemp()[1] + ".ttx"
    print("converting font file '{:s}' to '{:s}'".format(font_file, ttx_file))
    fontTools.ttx.main(["-o", ttx_file, font_file])

    skip_dates = set()
    if skip_list:
        with open(skip_list) as f:
            skip_dates = set(parse_date(l.strip()) for l in f)
        print()
        print("skiplist contained {} dates to skip".format(len(skip_dates)))

    print()
    print("checking font has all chars in text")
    font = ghht.TTF(ttx_file)
    for ch in text:
        font.assert_has(ch)
        print("'{}' ok".format(ch))

    print()
    print("generating commits")
    for (x, y), t in ghht.squares2commitdates(start_date, font.text2squares(text)):
        if t.date() in skip_dates:
            continue
        for _ in range(intensity):
            ghht.commit(t, sink_repo, "({},{})".format(x, y))

    if background:
        print()
        print("generating commits for background")
        ghht.commit_year(start_date.year, sink_repo)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sink_repo",
        type=str,
        help="Path to a git repository to be used for generating commits.")
    parser.add_argument("text",
        type=str,
        help="ASCII text to render on commit heatmap.")
    parser.add_argument("start_date",
        type=parse_date,
        help="Date of first commit using format: yyyy-mm-dd")
    parser.add_argument("--font-file",
        type=str,
        default=ghht.DEFAULT_FONT,
        help="TTX-convertible font file.")
    parser.add_argument("--background",
        action="store_true",
        default=False,
        help="Generate a single commit on every day to paint a background.")
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
