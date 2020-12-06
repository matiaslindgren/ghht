from collections import namedtuple
from datetime import datetime, timedelta
from xml.etree.ElementTree import ElementTree
import os
import subprocess

from matplotlib.path import Path
import matplotlib.pyplot as plt
import numpy as np


class TTF:
    def __init__(self, ttx_path, px_step=200, font_height=4):
        with open(ttx_path) as f:
            elem_tree = ElementTree(file=f)
        self.glyphs = elem_tree.find("glyf")
        self.hmtx = elem_tree.find("hmtx")
        self.cmap = elem_tree.find("cmap")
        self.px_step = px_step
        self.font_height = font_height

    def charname(self, ch):
        code = hex(ord(ch))
        node = self.cmap.find("*/map/[@code='{}']".format(code))
        return node.get("name")

    def glyph(self, ch):
        return self.glyphs.find("TTGlyph/[@name='{}']".format(self.charname(ch)))

    def xy(self, pt):
        x = int(pt.get("x")) // self.px_step
        y = int(pt.get("y")) // self.px_step
        return x, y

    def charsize(self, ch):
        mtx = self.hmtx.find("mtx/[@name='{}']".format(self.charname(ch)))
        width = int(mtx.get("width")) // self.px_step
        height = int(self.glyph(ch).get("yMax", 0)) // self.px_step
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
            inner_points = inner_points.round()
            # Invert y-axis
            inner_points[:,1] = -inner_points[:,1] + self.font_height - 1
            yield inner_points

    def assert_has(self, ch):
        assert self.glyph(ch) is not None, "font has no char '{}'".format(ch)

    def text2squares(self, text):
        for ch in text:
            self.assert_has(ch)
            yield self.charsize(ch), self.char2squares(ch)


Padding = namedtuple("Padding", ("top", "right", "left"))


class HeatMapCanvas:
    shape = (7, 53)

    @staticmethod
    def topleft(year):
        d = datetime(year=year, month=1, day=1)
        first_sunday = d + timedelta(days=6-d.weekday())
        return first_sunday

    @staticmethod
    def bottomright(year):
        d = datetime(year=year, month=12, day=31)
        last_sunday = d - timedelta(days=(1+d.weekday())%7)
        return last_sunday - timedelta(days=1)

    def __init__(self, year, padding):
        self.year = year
        self.padding = padding

        self.dx = 0

        begin = self.topleft(year)
        end = self.bottomright(year)
        begin_weeknum = int(begin.strftime("%U"))
        end_weeknum = int(end.strftime("%U"))
        weeks_delta = 1 + end_weeknum - begin_weeknum
        assert 0 < weeks_delta <= self.shape[1]
        self.weeks_delta = weeks_delta
        self.begin_date = begin

    def is_inside(self, x):
        return x + self.dx + self.padding.left < self.weeks_delta - self.padding.right

    def xy2date(self, x0, y0):
        x0, y0 = int(x0), int(y0)
        x = x0 + self.dx + self.padding.left
        y = y0 + self.padding.top
        return (x, y), self.begin_date + timedelta(weeks=x, days=y, hours=6)


def squares2commitdates(start_year, all_squares, padding):
    canvas = HeatMapCanvas(start_year, padding)
    for (char_width, height), char_squares in all_squares:
        if not canvas.is_inside(char_width):
            canvas = HeatMapCanvas(canvas.year - 1, padding)
        for squares in char_squares:
            for x, y in squares:
                yield canvas.xy2date(x, y)
        canvas.dx += char_width


def run(cmd, cwd):
    proc = subprocess.run(
            cmd.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            text=True)
    out = proc.stdout.strip()
    if out:
        print(out)
    proc.check_returncode()


def commit(date, sink_repo, msg):
    unix = round(date.timestamp())
    outpath = os.path.join(sink_repo, "commits.txt")
    with open(outpath, "a") as outf:
        print(unix, msg, file=outf)

    run("git add {:s}".format(os.path.basename(outpath)), sink_repo)
    run("git commit --date={:d} --message={:s}".format(unix, msg), sink_repo)


def commit_year(year, sink_repo):
    start = datetime(year=year, month=1, day=1)
    end = datetime(year=year+1, month=1, day=1)
    i = 1
    while start < end:
        commit(start, sink_repo, "bg-{:03d}".format(i))
        i += 1
        start += timedelta(days=1)


def plot_debug_heatmap(years):
    # https://matplotlib.org/3.1.1/gallery/images_contours_and_fields/image_annotated_heatmap.html
    fig, axes = plt.subplots(len(years), 1, squeeze=False, sharex=True)
    for ax, (year, data) in zip(axes, years):
        ax = ax[0]
        im = ax.imshow(data, cmap="Greens")
        ax.set_title(year)
        ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
        ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
        ax.grid(which="minor", color="w", linestyle='-', linewidth=1)
        ax.tick_params(which="minor", bottom=False, left=False)
    fig.tight_layout()
    plt.show()
