from xml.etree.ElementTree import ElementTree
from datetime import datetime, timedelta


class TTF:
    def __init__(self, ttx_path):
        with open(ttx_path) as f:
            elem_tree = ElementTree(file=f)
        self.glyphs = elem_tree.find("glyf")

    def glyph(self, n):
        return self.glyphs.find("TTGlyph/[@name='{}']".format(n))

    def normalized_xy(self, g, pt):
        def num(k):
            return int(g.get(k))
        xMin = num("xMin")
        yMin = num("yMin")
        xMax = num("xMax")
        yMax = num("yMax")
        x = float((int(pt.get("x"))-xMin)/(xMax-xMin))
        y = float((int(pt.get("y"))-yMin)/(yMax-yMin))
        return x, y

    def char2contours(self, c):
        g = self.glyph(c)
        if g is None:
            return
        for cont in g.findall("contour"):
            yield [self.normalized_xy(g, pt) for pt in cont.findall("pt")]


def point2time(start: datetime, x: int, y: int) -> datetime:
    delta = timedelta(weeks=x, days=y)
    assert delta < timedelta(days=365)
    return start + delta
