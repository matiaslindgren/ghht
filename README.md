# GitHub Heatmap Text (GHHT)

Pretend the green squares on GitHub heatmaps are pixels and "render" text on them with this useless Python package.

![alt](./img/screenshot.png "GitHub contribution heatmap for year 2015 with a pattern that spells out 'HELLO.' in capital letters in green colour")

## Install

```bash
python3 -m pip install --user https://github.com/matiaslindgren/ghht/archive/v0.5.1.zip
```

## Examples

```bash
python3 -m ghht -h
```

### Git commits

Create an empty directory (or use an existing git repo) and fill it with some commits:
```bash
mkdir commit-sink
python3 -m ghht "hello." 2015 --pad-left 8 --git-repo ./commit-sink
```
Then push `commit-sink` to a repository on GitHub.

### ASCII output

Run with `--ascii` to print results to stdout instead of generating commits.
```bash
python3 -m ghht 'haha wow! :DDD' 2014 --ascii
```
Output:
```
2014

 #  #  ##  #  #  ##       #  #  ##  #  #  #
 #  # #  # #  # #  #      #  # #  # #  #  #
 #### #### #### ####      #  # #  # #  #  #
 #  # #  # #  # #  #      #### #  # ####
 #  # #  # #  # #  #      #  #  ##  #  #  #
2013

           ###  ###  ###
       #   #  # #  # #  #
           #  # #  # #  #
       #   #  # #  # #  #
           ###  ###  ###
```
