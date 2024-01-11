from setuptools import setup

setup(
    name="ghht",
    version="0.5.1",
    install_requires=["fonttools ~= 4.18.0"],
    packages=["ghht"],
    package_data={"ghht": ["font/*.ttf", "font/*.txt"]},
    entry_points={"console_scripts": ["ghht = ghht.__main__:main"]},
)
