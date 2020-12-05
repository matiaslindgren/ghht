from datetime import datetime, timedelta
from xml.etree.ElementTree import ElementTree
import os
import subprocess

from matplotlib.path import Path
import numpy as np


class TTF:
    def __init__(self, ttx_path, px_step=200):
        with open(ttx_path) as f:
            elem_tree = ElementTree(file=f)
        self.glyphs = elem_tree.find("glyf")
        self.hmtx = elem_tree.find("hmtx")
        self.px_step = px_step

    def glyph(self, n):
        return self.glyphs.find("TTGlyph/[@name='{}']".format(n))

    def xy(self, pt):
        x = int(pt.get("x")) // self.px_step
        y = int(pt.get("y")) // self.px_step
        return x, y

    def charsize(self, ch):
        mtx = self.hmtx.find("mtx/[@name='{}']".format(ch))
        width = int(mtx.get("width")) // self.px_step
        height = int(self.glyph(ch).get("yMax")) // self.px_step
        return width, height

    def char2squares(self, ch):
        g = self.glyph(ch)
        if g is None:
            return

        for contour in g.findall("contour"):
            p = Path([self.xy(pt) for pt in contour.findall("pt")])
            min_x, min_y = p.vertices.min(axis=0).astype(np.int32)
            max_x, max_y = p.vertices.max(axis=0).astype(np.int32)

            # Grid of all points inside the rectangle defined by (min_x, min_y) (max_x, max_y)
            grid = np.meshgrid(np.arange(min_x, max_x), np.arange(min_y, max_y))
            grid_xy = np.dstack(grid).reshape(-1, 2)

            # All points that are in the middle of a square inside the contour
            inner_points = grid_xy[p.contains_points(grid_xy + 0.5)]
            yield inner_points.round()

    def text2squares(self, text):
        for ch in text:
            if ch == " ":
                # Whitespace has unit width, no height, and no pixels
                yield (1, 0), []
                continue
            assert self.glyph(ch) is not None, "font has no char '{}'".format(ch)
            yield self.charsize(ch), self.char2squares(ch)


def squares2commitdates(start_date, all_squares):
    dx = 0
    for (width, height), char_squares in all_squares:
        for squares in char_squares:
            for x, y in squares:
                x, y = int(x) + dx, -int(y) + height
                yield (x, y), start_date + point2timedelta(x, y)
        dx += width


def point2timedelta(x, y):
    assert 0 <= x < 60
    assert 0 <= y < 7
    return timedelta(weeks=x, days=y, hours=6)


def commit(date, sink_repo, msg):
    def run(cmd):
        proc = subprocess.run(
                cmd.split(' '),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=sink_repo,
                text=True)
        out = proc.stdout.strip()
        if out:
            print(out)
        proc.check_returncode()

    if not os.path.isdir(os.path.join(sink_repo, ".git")):
        print("'{}' does not have a .git directory, initializing repo".format(sink_repo))
        run("git init")

    unix = round(date.timestamp())
    outpath = os.path.join(sink_repo, "commits.txt")
    with open(outpath, "a") as outf:
        print(unix, msg, file=outf)

    run("git add {:s}".format(outpath))
    run("git commit --date={:d} --message={:s}".format(unix, msg))


def commit_year(year, sink_repo):
    start = datetime(year=year, month=1, day=1)
    end = datetime(year=year, month=12, day=31)
    i = 1
    while start < end:
        commit(start, sink_repo, "bg-{:03d}".format(i))
        i += 1
        start += timedelta(days=1)
