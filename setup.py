from setuptools import setup

setup(
    name="ghht",
    version="0.1.0",
    install_requires=[
        "fonttools ~= 4.18.0",
        "matplotlib ~= 3.3.3",
        "numpy ~= 1.19.4",
    ],
    packages=[
        "ghht",
    ],
    package_data={
        "ghht": ["fonts/tiny/*.ttf", "fonts/tiny/*.txt"],
    },
    entry_points={
        "console_scripts": [
            "ghht = ghht.__main__:main",
        ],
    },
)
