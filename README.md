Feel free to open a Github issue if you have any problems running the code
---
# LocationCrawler
A non API python program to scrape number of posts at a location, as well as locations in a city
### Full usage:
```
usage: python LocationCrawler.py [-l LOCATION] [-t TIMEWINDOW]
```
"-d", "--date", type=str, default="now", help="Date up till which to scrape"
"-l", "--location", type=str, default="no", help="Location Number eg. 214335386 for Englischer Garten"
"-t", "--timeWindow", type=float, default=1.0, help="Timeframe to check number of posts in hours eg. 1"
"-c", "--city", type=str, default="no", help="City to scrape location links from, eg c579270 for Munich"
"-dir", "--dirPrefix", type=str, default="./data/", help="directory to save results"


### Installation
download chromedriver here: https://sites.google.com/a/chromium.org/chromedriver/
put the executable into the same directory as instagramcrawler.py and rename it to chromedriverWIN or chromedriverMAC depending on your version

There are 2 packages : selenium & requests
```
$ pip install -r requirements.txt
```
