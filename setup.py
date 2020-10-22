from setuptools import find_packages, setup


setup(
    name='mangadown',
    version="0.1.0",
    description='Automated manga scan downloader',
    url='https://github.com/Zeletochoy/mangadown',
    author='Antoine Lecubin',
    author_email='antoinelecubin@msn.com',
    packages=find_packages(),
    license="beerware",
    install_requires=[
        "aiohttp[speedups]>=3.6.2",
        "attrs>=20.2.0",
        "beautifulsoup4>=4.9.2",
        "certifi>=2020.6.20",
        "click>=6.7",
        "cloudscraper>=1.2.48",
        "KindleComicConverter>=5.5.2",
        "Pillow>=7.2.0",
        "psutil>=5.7.2",
        "requests>=2.24.0",
    ],
    entry_points={
        "console_scripts": [
            "mangadown=mangadown.cli.mangadown:main",
            "sendmails=mangadown.cli.sendmails:main",
        ],
    },
)
