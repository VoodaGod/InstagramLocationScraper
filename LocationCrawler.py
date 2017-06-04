import argparse
from sys import platform
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
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

#Element locators
LOAD_MORE = (By.CSS_SELECTOR, "a._8imhp._glz1g")
DATE = (By.CSS_SELECTOR, "time")
CLOSE_BUTTON = (By.CLASS_NAME, "_3eajp")
SEE_MORE = (By.CLASS_NAME, "_jn623")

#Class names
LOCATION_LINK = "_3hq20"
POST = "_ovg3g"

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

	def clickElement(self, locator=(), element=None):
		try:
			if(locator != ()):
				WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(locator)).click()
			if(element != None):
				element.click()
			return True
		except TimeoutException:
			return False
		except WebDriverException:
			print("try clicking higher")
			try:
				webdriver.ActionChains(self.driver).move_to_element_with_offset(element, 0, 20).click().perform()
				return True
			except:
				traceback.print_exc()
				return False

	#scrolls until an imager older than dateFrom is found
	def scrollToDate(self, dateFrom):
		self.driver.execute_script(SCROLL_DOWN)
		loaded = False
		while(True):
			postList = self.driver.find_elements_by_class_name(POST)
			self.clickElement(element=postList[-1])
			dateElement = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(DATE))
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			self.clickElement(locator=CLOSE_BUTTON)
			if(date <= dateFrom):
				return postList
			self.driver.execute_script(SCROLL_DOWN)
			if(not loaded):
				self.clickElement(LOAD_MORE)
				loaded = True
			time.sleep(0.1)

	def binaryDateSearch(self, dateCmp, postList, left, right):
		while(True):
			middle = int((left + right) / 2)
			self.clickElement(element=postList[middle])
			try:
				dateElement = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(DATE))
			except TimeoutException:
				print("couldn't locate date element")
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			self.clickElement(locator=CLOSE_BUTTON)
			if(date > dateCmp):
				left = middle + 1
			elif(date < dateCmp):
				right = middle - 1
			if(right < left):
				return left

	def findFirstPost(self, dateFrom, postList):
		#binary search on last 12 loaded posts, as posts[-13] is younger than dateFrom
		left = len(postList) - 12
		right = len(postList) - 1
		match = self.binaryDateSearch(dateFrom, postList, left, right)
		return match

	def findLastPost(self, dateTo, postList, firstPostIndex):
		#binary search
		left = 9 #first 9 posts are "top posts"
		right = firstPostIndex
		match = self.binaryDateSearch(dateTo, postList, left, right)
		return match

	def scrapeCity(self, city):
		self.browseTargetPage(city)
		while(True):
			self.driver.execute_script(SCROLL_DOWN)
			if(not self.clickElement(locator=SEE_MORE)):
				break
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
		except:
			print("\nException in: " + self.name + ", " + self.args[1])
			traceback.print_exc()
			print("")
		finally:
			self.scraperFree = True


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

	start = datetime.now()

	if((args.fromList[0] != "no") and (args.fromList[1] != "no")):
		cities, locs = False, False
		if(args.fromList[1] == "c"):
			cities = True
		elif(args.fromList[1] == "l"):
			locs = True

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

			i = 0
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
			print("\nException in mainthread: ")
			#traceback.print_exc()
			print("")
			raise
		finally:
			for s in scrapers:
				s.quit()

	else:
		scraper = LocationScraper()
		try:
			if(args.city != "no"):
				scrapeCityToFile(args.dirPrefix, args.city, scraper)

			if(args.location != "no"):
				scrapeLocationToFile(args.dirPrefix, args.location, args.date, args.timeWindow, scraper)
		except:
			#traceback.print_exc()
			raise
		finally:
			scraper.quit()

	end = datetime.now()
	print ("elapsed time: " + str(end - start))

main()