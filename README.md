
# LocationCrawler
A non API python program to scrape number of posts at a location, as well as locations in a city
### Full usage:
```
usage: LocationCrawler.py [-h] [-d DATE] [-l LOCATION] [-t TIMEWINDOW]
                          [-c CITY] [-dir DIRPREFIX]
```

Instagram Location Scraper

optional arguments:
  -h, --help         show this help message and exit
  -d, --date         Date up till which to scrape, eg. 2017-06-01T10:00:00
  -l, --location     Location Number to scrape, eg. 214335386 for Englischer Garten
  -t, --timeWindow   Timeframe to check number of posts in hours, eg. 1.0
  -c, --city         City to scrape location links from, eg c579270 for Munich
  -dir, --dirPrefix  directory to save results, default: ./data/


### Installation
download chromedriver here: https://sites.google.com/a/chromium.org/chromedriver/
put the executable into the same directory as instagramcrawler.py and rename it to chromedriverWIN or chromedriverMAC depending on your version

```
$ pip install -r requirements.txt
```
