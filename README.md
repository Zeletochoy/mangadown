Automated manga downloader
==========================

Rewrite in progress...
Mostly working now.


# Setup


* Get python 3 and pip
* `pip install .`
* Fill your MyAnimeList credentials in settings.py
* Create a `tracked` file with the mangas you want to track
    * One per line
    * Supported names given by `mangadown.py -l`
    * Lines starting with # are ignored


# TODO


* Ad removal (simple MD5 check?)
* Cleaning and kindle conversion
  * Splitting : both?
  * Set author from MAL
* Service to watch new releases
