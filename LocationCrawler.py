import argparse
from sys import platform
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from datetime import timedelta
import dateutil.parser
import traceback
import os
import threading


# URLS
HOST = "https://www.instagram.com"
RELATIVE_URL_LOCATION = "/explore/locations/"
DEFAULT_URL = "about:blank"

# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = "a._8imhp._glz1g"
CSS_DATE = "a time"

# CLASS NAMES
CLOSE_BUTTON = "_3eajp"
POST = "_ovg3g"
SEE_MORE = "_jn623"
LOCATION_LINK = "_3hq20"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"

#path for the scraper profile
CHROME_PROFILE_PATH = "./Scraper"

class LocationScraper(object):
	def __init__(self, profilePath=CHROME_PROFILE_PATH):
		options = webdriver.ChromeOptions()
		prefs = {"profile.managed_default_content_settings.images":2}
		options.add_argument("user-data-dir=" + profilePath)
		options.add_argument("headless")
		options.add_argument('window-size=1200x600')
		options.add_experimental_option("prefs", prefs)

		if platform == "win32":
			self.driver = webdriver.Chrome(executable_path="./chromedriverWIN.exe", chrome_options=options)
		elif platform == "darwin":
			self.driver = webdriver.Chrome(executable_path="./chromedriverMAC", chrome_options=options)
		else:
			print("neither Windows nor Mac detected")

	def quit(self):
		self.driver.quit()

	def scrapeLocation(self, location, dateTo, dateFrom):
		self.browseTargetPage(location)
		postList = self.scrollToDate(dateFrom)
		if(len(postList) <= 9):
			return 0 #only top posts
		firstPostIndex = self.findFirstPost(dateFrom, postList)
		lastPostIndex = self.findLastPost(dateTo, postList, firstPostIndex)
		return (firstPostIndex - lastPostIndex)

	def browseTargetPage(self, location):
		targetURL = HOST + RELATIVE_URL_LOCATION + location
		self.driver.get(targetURL)

	#scrolls until an imager older than dateFrom is found
	def scrollToDate(self, dateFrom):
		self.driver.execute_script(SCROLL_DOWN)
		try:
			loadmore = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_LOAD_MORE)))
		except: #TimeoutException:
			pass
		else:
			loadmore.click()
		while(True):
			postList = self.driver.find_elements_by_class_name(POST)
			postList[-1].click()
			dateElement = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_DATE)))
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			closeButton = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, CLOSE_BUTTON)))
			closeButton.click()
			if(date <= dateFrom):
				return postList
			self.driver.execute_script(SCROLL_DOWN)
			time.sleep(0.1)

	def findFirstPost(self, dateFrom, postList):
		#start looking from the back
		for i in range(1, (len(postList) - 9)):
			postList[-i].click()
			dateElement = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_DATE)))
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			closeButton = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, CLOSE_BUTTON)))
			closeButton.click()
			if (date >= dateFrom):
				return len(postList) - i
		return 9 #no posts since dateFrom, return first post in "most recent"

	def findLastPost(self, dateTo, postList, firstPostIndex):
		#binary search
		left = 9
		right = firstPostIndex
		while(True):
			middle = int((left + right) / 2)
			if(right < left):
				return left
			if(left > right):
				return right
			postList[middle].click()
			try:
				dateElement = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_DATE)))
			except TimeoutException:
				continue
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			closeButton = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, CLOSE_BUTTON)))
			closeButton.click()
			if(date > dateTo):
				left = middle + 1
			elif(date < dateTo):
				right = middle - 1

	def scrapeCity(self, city):
		self.browseTargetPage(city)
		while(True):
			self.driver.execute_script(SCROLL_DOWN)
			try:
				seeMore = WebDriverWait(self.driver,5).until(EC.presence_of_element_located((By.CLASS_NAME, SEE_MORE)))
			except TimeoutException:
				break
			seeMore.click()
			time.sleep(0.75)

		locationLinks = []
		for element in self.driver.find_elements_by_class_name(LOCATION_LINK):
			locationLinks.append(element.get_attribute("href").replace(HOST + RELATIVE_URL_LOCATION, ""))
		return locationLinks


def scrapeCityToFile(dirPrefix, city, scraper):
	path = dirPrefix + "Locations/" + city.replace("/","_") + "Locations.txt"
	print("scraping city: " + city + " for locations to " + path)
	locations = scraper.scrapeCity(city)

	os.makedirs(os.path.dirname(path), exist_ok=True)
	file = open(path, "w")
	for loc in locations:
		file.write(loc+ "\n")
	file.close()

def scrapeLocationToFile(dirPrefix, location, date, timeWindow, scraper):
	if(date == "now"):
		dateTo = datetime.utcnow()
	else:
		dateTo = dateutil.parser.parse(date, ignoretz=True)
	dateFrom = dateTo - timedelta(hours=timeWindow)
	if(dateTo > datetime.utcnow()):
		print("waiting until " + dateTo.isoformat())
		while(dateTo > datetime.utcnow()):
			time.sleep(10)

	path = dirPrefix + "Postcounts/" + location.replace("/","_") + "Postcounts.txt"
	print("Scraping location " + location + " for number of pictures posted between " + str(dateFrom) + " and " + str(dateTo) + " to " + path)
	numPosts = scraper.scrapeLocation(location=location, dateTo=dateTo, dateFrom=dateFrom)

	print(location + ": " + str(numPosts))
	os.makedirs(os.path.dirname(path), exist_ok=True)
	file = open(path, "a+")
	file.write(dateTo.isoformat() + "\t" + str(numPosts) + "\n")
	file.close()


class ScrapeThread(threading.Thread):
	def __init__(self, target, args, scraper):
		threading.Thread.__init__(self)
		self.target = target
		self.args = args
		self.scraperFree = False
		self.scraper = scraper

	def run(self):
		try:
			self.target(*self.args)
			self.scraperFree = True
		except:
			traceback.print_exc()
			self.scraper.quit()


def main():
	#   Arguments  #
	parser = argparse.ArgumentParser(description="Instagram Location Scraper")
	parser.add_argument("-d", "--date", type=str, default="now", help="Date up till which to scrape, eg. 2017-06-01T10:00:00")
	parser.add_argument("-l", "--location", type=str, default="no", help="Location Number to scrape, eg. 214335386 for Englischer Garten")
	parser.add_argument("-t", "--timeWindow", type=float, default=1.0, help="Timeframe to check number of posts in hours, eg. 1.0")
	parser.add_argument("-c", "--city", type=str, default="no", help="City to scrape location links from, eg. c579270 for Munich")
	parser.add_argument("-dir", "--dirPrefix", type=str, default="./data/", help="directory to save results, default: ./data/")
	parser.add_argument("-list", "--fromList", default=["no", "no"], nargs=2, help="File containing a list of locations/cities to scrape, specify with c or l, eg. -list c")
	parser.add_argument("-threads", "--threadCount", type=int, default=1, help="how many threads to use")

	args = parser.parse_args()
	#  End Argparse #

	if((args.fromList[0] != "no") and (args.fromList[1] != "no")):
		cities, locs = False, False
		if(args.fromList[1] == "c"):
			cities = True
		elif(args.fromList[1] == "l"):
			locs = True

		start = datetime.now()

		try:
			file = open(args.fromList[0])
			lines = []
			lines.append(file.readline().strip('\n'))
			while(lines[-1] != ""):
				lines.append(file.readline().strip('\n'))
			lines.pop()
			file.close()

			print("Starting Scrapers")
			scrapers= []
			threads = []
			i = 0
			while(i < min(args.threadCount, len(lines))):
				scrapers.append(LocationScraper(profilePath=CHROME_PROFILE_PATH + str(i)))
				if(cities):
					threads.append(ScrapeThread(target=scrapeCityToFile, args=(args.dirPrefix, lines[i], scrapers[i]), scraper=scrapers[i]))
				elif(locs):
					threads.append(ScrapeThread(target=scrapeLocationToFile, args=(args.dirPrefix, lines[i], args.date, args.timeWindow, scrapers[i]), scraper=scrapers[i]))
				threads[i].start()
				i += 1

			while(True):
				if(threading.active_count() <= args.threadCount):
					if(i > (len(lines) - 1)):
						break
					for t in threads:
						if(t.scraperFree):
							t.scraperFree = False
							if(cities):
								threads.append(ScrapeThread(target=scrapeCityToFile, args=(args.dirPrefix, lines[i], t.scraper), scraper=t.scraper))
							elif(locs):
								threads.append(ScrapeThread(target=scrapeLocationToFile, args=(args.dirPrefix, lines[i], args.date, args.timeWindow, t.scraper), scraper=t.scraper))
							threads[-1].start()
							i += 1
							break
				time.sleep(0.5)

			for t in threads:
				t.join()

		except:
			for s in scrapers:
				s.quit()
			traceback.print_exc()

		for s in scrapers:
			s.quit()

		end = datetime.now()
		print ("elapsed time: " + str(end - start))

	else:
		scraper = LocationScraper()
		try:
			if(args.city != "no"):
				scrapeCityToFile(args.dirPrefix, args.city, scraper)

			if(args.location != "no"):
				scrapeLocationToFile(args.dirPrefix, args.location, args.date, args.timeWindow, scraper)
		except:
			traceback.print_exc()
		finally:
			scraper.quit()

main()