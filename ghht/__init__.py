import os
DEFAULT_FONT = os.path.join(__path__[0], "fonts", "tiny", "tiny.ttf")

from .ghht import (
    TTF,
    commit,
    commit_year,
    squares2commitdates,
)
