from datetime import datetime
import argparse
import contextlib
import io
import os
import tempfile
import sys

import fontTools.ttx
import ghht


def parse_date(d):
    return datetime.datetime.strptime(d, "%Y-%m-%d")


def run_ghht(
    git_repo,
    text,
    start_year,
    font_file,
    background,
    intensity,
    ascii,
    verbose,
):
    assert git_repo or ascii, "specify either --git-repo or --ascii"
    ttx_file = tempfile.mkstemp()[1] + ".ttx"
    if verbose:
        print(f"converting font file '{font_file:s}' to '{ttx_file:s}'")
    with contextlib.redirect_stdout(io.StringIO()) as f:
        with contextlib.redirect_stderr(sys.stdout):
            fontTools.ttx.main(["-o", ttx_file, font_file])
            if verbose:
                print(f.getvalue())

    if verbose:
        print(f"checking font has all chars in text '{text}'")
    font = ghht.TTF(ttx_file)
    for ch in text:
        font.assert_has(ch)
        if verbose:
            print(f"'{ch}' ok")

    xy_dates = list(
        ghht.squares2commitdates(
            start_year,
            font.text2squares(text),
            ghht.Padding(top=2, right=1, left=1),
        )
    )

    if ascii:
        if verbose:
            print("ascii mode, will not generate commits")
        for row in ghht.as_ascii_rows(xy_dates):
            print(row)
        return

    if not os.path.isdir(os.path.join(git_repo, ".git")):
        if verbose:
            print(f"'{git_repo}' does not have a .git directory, initializing repo")
        ghht.run("git init", git_repo)

    if verbose:
        print("generating commits")
    for (x, y), t in xy_dates:
        for _ in range(intensity):
            ghht.commit(t, git_repo, f"({x},{y})")

    if background:
        if verbose:
            print("generating commits for background")
        ghht.commit_year(start_year, git_repo)


def main():
    parser = argparse.ArgumentParser(prog=ghht.__name__)
    parser.add_argument(
        "text",
        type=str,
        help="Short ASCII text to render on commit heatmap.",
    )
    parser.add_argument(
        "start_year",
        type=int,
        help="Year for first commit.",
    )
    parser.add_argument(
        "--git-repo",
        type=str,
        help="Path to a git repository or directory (runs git init automatically if there's no .git dir) to be used for generating commits.",
    )
    parser.add_argument(
        "--font-file",
        type=str,
        default=ghht.DEFAULT_FONT,
        help="TTX-convertible font file.",
    )
    parser.add_argument(
        "--background",
        action="store_true",
        default=False,
        help="Generate a single commit on every day to paint a background.",
    )
    parser.add_argument(
        "--ascii",
        action="store_true",
        default=False,
        help="Print results to stdout instead of generating commits.",
    )
    parser.add_argument(
        "--intensity",
        type=int,
        default=1,
        help="How many commits to generate for every text square.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
    )
    run_ghht(**vars(parser.parse_args()))


if __name__ == "__main__":
    main()
