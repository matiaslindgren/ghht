from collections import namedtuple, defaultdict
from datetime import datetime, timedelta
from xml.etree.ElementTree import ElementTree
import os
import subprocess


def interpolate(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    dx = 1 if x1 == x2 else (x2 - x1) // abs(x2 - x1)
    dy = 1 if y1 == y2 else (y2 - y1) // abs(y2 - y1)
    for x in range(x1, x2 + dx, dx):
        for y in range(y1, y2 + dy, dy):
            yield x, y


def minmax_xy(points):
    x_min = y_min = float("inf")
    x_max = y_max = -float("inf")
    for x, y in points:
        x_min = min(x_min, x)
        x_max = max(x_max, x)
        y_min = min(y_min, y)
        y_max = max(y_max, y)
    return x_min, x_max, y_min, y_max


def flood_fill(contour):
    x_min, x_max, y_min, y_max = minmax_xy(contour)
    not_contour = {
        (x, y)
        for x in range(x_min - 1, x_max + 2)
        for y in range(y_min - 1, y_max + 2)
        if (x, y) not in contour
    }
    q = [next(iter(not_contour))]
    visited = set()
    inside = True
    while q:
        p = q.pop()
        if p not in not_contour or p in visited:
            continue
        visited.add(p)
        x, y = p
        if x < x_min or y < y_min or x_max < x or y_max < y:
            inside = False
        q.append((x - 1, y))
        q.append((x + 1, y))
        q.append((x, y - 1))
        q.append((x, y + 1))
    return sorted(visited if inside else not_contour - visited)


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
            # Collect all points on the contour and flood fill interior
            p = [
                (2 * x, 2 * y) for x, y in (self.xy(pt) for pt in contour.findall("pt"))
            ]
            points = []
            for p1, p2 in zip(p, p[1:] + [p[0]]):
                points.extend(interpolate(p1, p2))
                points.pop()
            points = set((x // 2, y // 2) for x, y in flood_fill(points))
            # Invert y-axis
            yield [(x, -y + self.font_height - 1) for x, y in points]

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
        first_sunday = d + timedelta(days=6 - d.weekday())
        return first_sunday

    @staticmethod
    def bottomright(year):
        d = datetime(year=year, month=12, day=31)
        last_sunday = d - timedelta(days=(1 + d.weekday()) % 7)
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


def sys_run(cmd, cwd):
    proc = subprocess.run(
        cmd.split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        text=True,
    )
    out = proc.stdout.strip()
    if out:
        print(out)
    proc.check_returncode()


def commit(date, sink_repo, msg):
    unix = round(date.timestamp())
    outpath = os.path.join(sink_repo, "commits.txt")
    with open(outpath, "a") as outf:
        print(unix, msg, file=outf)
    sys_run("git add {:s}".format(os.path.basename(outpath)), sink_repo)
    sys_run("git commit --date={:d} --message={:s}".format(unix, msg), sink_repo)


def commit_year(year, sink_repo):
    start = datetime(year=year, month=1, day=1)
    end = datetime(year=year + 1, month=1, day=1)
    i = 1
    while start < end:
        commit(start, sink_repo, "bg-{:03d}".format(i))
        i += 1
        start += timedelta(days=1)


def as_ascii_rows(xy_dates):
    x_min, x_max, y_min, y_max = minmax_xy(xy for xy, _ in xy_dates)
    years = defaultdict(
        lambda: [[" " for x in range(x_max + 1)] for y in range(y_max + 1)]
    )
    for (x, y), td in xy_dates:
        years[td.year][y][x] = "#"
    for year, grid in years.items():
        yield format(year, "d")
        for row in grid:
            yield "".join(row)
