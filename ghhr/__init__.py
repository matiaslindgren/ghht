from xml.etree.ElementTree import ElementTree
from datetime import datetime, timedelta
from matplotlib.path import Path
import numpy as np


class TTF:
    def __init__(self, ttx_path, px_step=200):
        with open(ttx_path) as f:
            elem_tree = ElementTree(file=f)
        self.glyphs = elem_tree.find("glyf")
        self.px_step = px_step

    def glyph(self, n):
        return self.glyphs.find("TTGlyph/[@name='{}']".format(n))

    def xy(self, pt):
        x = int(pt.get("x")) // self.px_step
        y = int(pt.get("y")) // self.px_step
        return x, y

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


def text2squares(text):
    font = TTF("fonts/tiny/tiny.ttx")
    for ch in text:
        if ch == " ":
            yield [(None, None)]
            continue
        assert font.glyph(ch) is not None, "font has no char '{}'".format(ch)
        yield font.char2squares(ch)


def squares2commits(start_time, squares):
    for char_squares in squares:
        # One character
        for squares in char_squares:
            for x, y in squares:
                t = point2time(start_time, int(x), int(y))
                commit(t)


def commit(time):
    print("commit", time)


def point2time(start: datetime, x: int, y: int) -> datetime:
    delta = timedelta(weeks=x, days=y)
    assert delta < timedelta(days=365)
    return start + delta
