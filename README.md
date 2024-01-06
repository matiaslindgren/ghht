# GitHub Heatmap Text (GHHT)

Pretend the green squares on GitHub heatmaps are pixels and "render" text on them with this useless Python package.

![alt](./img/screenshot.png "GitHub contribution heatmap for year 2015 with a pattern that spells out 'HELLO GITHUB' in capital letters in green colour")

## Install

```bash
python3 -m pip install --user https://github.com/matiaslindgren/ghht/archive/v0.3.2.zip
```

## Examples

```bash
python3 -m ghht -h
```

### Git commits

Create an empty directory and fill it with some commits:
```bash
mkdir commit-sink
python3 -m ghht "HELLO GITHUB" 2015 --git-repo ./commit-sink
```
Then create a repository on GitHub and push `commit-sink` there.

### ASCII output

Run with `--ascii` to print results to stdout instead of generating commits.
```bash
python3 -m ghht "python3 -c   'import this'" 1999 --ascii
```
Output:
```
1999


          #  #           ##
 ##  # # ### ##   #  ##   ##         ##
 # # ###  #  # # # # # #   #    ### #
 ##    #  #  # #  #  # # ##          ##
 #   ##
1998


 # #                   #      #  #   #     #
 #   ## #  ##   #  ## ###    ### ##     ## #
   # # # # # # # # #   #      #  # # #  #
   # # # # ##   #  #   #      #  # # # ##
           #
```
