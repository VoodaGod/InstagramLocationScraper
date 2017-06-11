
# LocationCrawler
A non API python program to scrape number of posts at a location, as well as locations in a city
I am coding this for use in my Seminar "Computational Social Sciences" to acquire data for my group
### Full usage:
```
usage: LocationCrawler.py [-h] [-l LOCATION] [-c CITY] [-fromFile FILE TYPE]
                          [-fromDir DIR SUFFIX] [-d DATE] [-t TIMEWINDOW]
                          [-dir DIRPREFIX] [-threads THREADCOUNT]
                          [-max MAXPOSTS] [-drv DRIVERPATH]
                          [-drvProfile DRIVERPROFILEPREFIX]

Instagram Location Scraper

optional arguments:
  -h, --help            show this help message and exit
  -l LOCATION, --location LOCATION
                        Location Number to scrape, eg. 214335386/ for
                        Englischer Garten
  -c CITY, --city CITY  City to scrape location links from, eg. c579270/ for
                        Munich
  -fromFile FILE TYPE   File containing a list of locations/cities to scrape,
                        specify with c or l, eg. -list cities.txt c
  -fromDir DIR SUFFIX   Directory containing files with lists of locations to
                        scrape with suffix to specify which files to scrape,
                        eg. -lDir ./data/Locations _Locations.txt
  -d DATE, --date DATE  Date up till which to scrape, eg. 2017-06-01T10:00:00
  -t TIMEWINDOW, --timeWindow TIMEWINDOW
                        Timeframe to check number of posts in hours, eg. 1.0
  -dir DIRPREFIX, --dirPrefix DIRPREFIX
                        directory to save results to, default: ./data/
  -threads THREADCOUNT, --threadCount THREADCOUNT
                        how many threads to use
  -max MAXPOSTS, --maxPosts MAXPOSTS
                        maximum number of posts to scrape, eg. due to
                        performance reasons
  -drv DRIVERPATH, --driverPath DRIVERPATH
                        path to chromedriver, default = ./chromedriver.exe
  -drvProfile DRIVERPROFILEPREFIX, --driverProfilePrefix DRIVERPROFILEPREFIX
                        prefix for scraper chrome profiles, default =
                        ./Scraper
```

### Installation
download chromedriver here: https://sites.google.com/a/chromium.org/chromedriver/
put the executable into the same directory as instagramcrawler.py and rename it to chromedriverWIN or chromedriverMAC depending on your version

```
$ pip install -r requirements.txt
```
