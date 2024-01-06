from setuptools import setup

setup(
    name="ghht",
    version="0.3.0",
    install_requires=[
        "fonttools ~= 4.18.0",
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
