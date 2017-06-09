import argparse
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
CHROMEDRIVER_PATH = "./chromedriver.exe"

class LocationScraper(object):
	def __init__(self, profilePath, driverPath):
		options = webdriver.ChromeOptions()
		prefs = {"profile.managed_default_content_settings.images":2}
		options.add_argument("user-data-dir=" + profilePath)
		options.add_argument("headless")
		options.add_argument('window-size=1920x1080')
		options.add_experimental_option("prefs", prefs)

		try:
			self.driver = webdriver.Chrome(executable_path=driverPath, chrome_options=options)
		except:
			print("failed to start driver at " + driverPath)
			self.inUse = True #scraper with no driver is not ready to handle new job
			traceback.print_exc()

		self.inUse = False #if False, is ready to handle new job

	def quit(self):
		"""quit the driver"""
		self.driver.quit()

	def scrapeLocation(self, location, dateTo, dateFrom, maxPosts):
		"""return number of posts at location since dateFrom till dateTo, scrolling at most to maxPosts"""
		self.browseLocationPage(location)
		postList = self.scrollToDate(dateFrom, maxPosts)
		if(len(postList) <= 9): #no recent posts, only "top posts" or none
			return 0
		firstPostIndex = self.findFirstPost(dateFrom, postList)
		lastPostIndex = self.findLastPost(dateTo, postList, firstPostIndex)
		if(len(postList) == (maxPosts + 9)): #didn't finish scrolling
			return -(firstPostIndex - lastPostIndex) #negative = more than
		else:
			return (firstPostIndex - lastPostIndex)

	def scrapeCity(self, city):
		"""return list of relative urls of all locations in a city"""
		self.browseLocationPage(city)
		while(True):
			self.driver.execute_script(SCROLL_DOWN)
			time.sleep(0.1)
			if(not self.clickElement(locator=SEE_MORE)):
				break
			time.sleep(0.75) #seems to get duplicate elements when looping too fast

		locationLinks = []
		for element in self.driver.find_elements_by_class_name(LOCATION_LINK):
			locationLinks.append(element.get_attribute("href").replace(HOST + RELATIVE_URL_LOCATION, ""))
		return locationLinks

	def browseLocationPage(self, location):
		"""browses a page with partial url relative to location url"""
		targetURL = HOST + RELATIVE_URL_LOCATION + location
		self.driver.get(targetURL)

	def clickElement(self, locator=(), element=None):
		"""returns True if successfully clicked an element by locator or reference"""
		el = None
		try: #click normally
			if(locator != ()): #by locator
				try:
					el = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
					el.click()
					time.sleep(0.1)
					#webdriver.ActionChains(self.driver).send_keys_to_element(el, Keys.ENTER).perform()
					return True
				except TimeoutException:
					return False
			elif(element != None): #by element
				el = element
				el.click()
				time.sleep(0.1)
				return True
			return False #nothing to click

		except WebDriverException: #element wasn't clickable, try sending enter instead
			try:
				if(el == None):
					return False
				webdriver.ActionChains(self.driver).send_keys_to_element(el, Keys.ENTER).perform()
				time.sleep(0.1)
				return True
			except:
				traceback.print_exc()
				return False

	def scrollToDate(self, dateFrom, maxPosts):
		"returns list of posts since dateFrom, scrolling at most to maxPosts"
		self.clickElement(locator=(By.CLASS_NAME, "_8yoiv")) #email banner
		self.driver.execute_script(SCROLL_DOWN)
		loaded = False
		prevLength = 0
		scrollCounter = 0
		while(True):
			postList = self.driver.find_elements_by_class_name(POST)
			if(len(postList) < 9):
				return [] #no recent posts, only "top posts" or none
			if(not (len(postList) > prevLength)): #no new posts loaded yet
				self.driver.execute_script(SCROLL_DOWN)
				scrollCounter += 1
				time.sleep(0.25)
				if(scrollCounter > 10): #probably at end of list
					return postList
				else:
					continue
			else:
				scrollCounter = 0
			prevLength = len(postList)
			if(maxPosts >= 0): #return at most maxPost many recent posts
				while(len(postList) > (maxPosts + 9)):
					postList.pop()
				if(len(postList) == (maxPosts + 9)):
					return postList

			#if last element is older than dateFrom, return postList
			if (not self.clickElement(element=postList[-1])):
				self.clickElement(locator=CLOSE_BUTTON)
				continue
			try:
				dateElement = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(DATE))
			except TimeoutException:
				print("couldn't locate date element")
				continue
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			self.clickElement(locator=CLOSE_BUTTON)
			if(date <= dateFrom):
				return postList
			self.driver.execute_script(SCROLL_DOWN)
			if(not loaded): #haven't clicked "load more" yet
				self.clickElement(LOAD_MORE)
				loaded = True

	def binaryDateSearch(self, dateCmp, postList, left, right):
		"""return index for dateCmp in postList between left & right"""
		while(True):
			middle = int((left + right) / 2)
			self.clickElement(element=postList[middle])
			try:
				dateElement = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(DATE))
			except TimeoutException:
				self.clickElement(locator=CLOSE_BUTTON)
				continue
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			self.clickElement(locator=CLOSE_BUTTON)
			if(date == dateCmp):
				return middle
			elif(date > dateCmp):
				left = middle + 1
			elif(date < dateCmp):
				right = middle - 1
			if(right < left): #not sure why return left seems to work
				return left

	def findFirstPost(self, dateFrom, postList):
		"""returns index of first post in postList after dateFrom"""
		#binary search on last 12 loaded posts, as posts[-13] is younger than dateFrom
		if((len(postList) - 9) < 12):
			left = 9 #no full page of most recent with 12 posts
		else:
			left = len(postList) - 12 #only search in most recently loaded full page of most recent posts
		right = len(postList) - 1
		match = self.binaryDateSearch(dateFrom, postList, left, right)
		return match

	def findLastPost(self, dateTo, postList, firstPostIndex):
		"""returns last post in postList before dateTo"""
		#binary search between newest post & firstPostIndex
		left = 9 #first 9 posts are "top posts"
		right = firstPostIndex
		match = self.binaryDateSearch(dateTo, postList, left, right)
		return match


def scrapeCityToFile(dirPrefix, city, scraper):
	path = dirPrefix + "Locations/" + city.replace("/","_") + "Locations.txt"
	print("scraping city: " + city + " for locations to " + path)
	locations = scraper.scrapeCity(city)

	os.makedirs(os.path.dirname(path), exist_ok=True)
	file = open(path, "w")
	for loc in locations:
		file.write(loc+ "\n")
	file.close()

def scrapeLocationToFile(dirPrefix, location, date, timeWindow, maxPosts, scraper):
	if(date == "now"):
		dateTo = datetime.utcnow()
	else:
		dateTo = dateutil.parser.parse(date, ignoretz=True)
	dateFrom = dateTo - timedelta(hours=timeWindow)
	if(dateTo > datetime.utcnow()):
		print("waiting until " + dateTo.isoformat())
		while(dateTo > datetime.utcnow()):
			time.sleep(10)

	path = dirPrefix + "_Postcounts/" + location.replace("/","_") + "Postcounts.txt"
	print("Scraping location " + location + " for number of pictures posted between " + str(dateFrom) + " and " + str(dateTo) + " to " + path)
	numPosts = scraper.scrapeLocation(location, dateTo, dateFrom, maxPosts)

	print(location + ": " + str(numPosts))
	os.makedirs(os.path.dirname(path), exist_ok=True)
	file = open(path, "a+")
	file.write(dateTo.isoformat() + "\t" + str(numPosts) + "\n")
	file.close()

def getLinesInFile(filePath):
	lines = []
	try:
		file = open(filePath, "r")
	except FileNotFoundError:
		print("File not found")
		return lines
	else:
		lines.append(file.readline().strip('\n'))
		while(lines[-1] != ""):
			lines.append(file.readline().strip('\n'))
		lines.pop()
		file.close()
	return lines

def scrapeCitiesFromFile(filePath, dirPrefix, threadCount, scrapers):
	cities = getLinesInFile(filePath)
	scrapeCitiesFromList(cities, dirPrefix, threadCount, scrapers)

def scrapeLocationsFromFile(filePath, dirPrefix, date, timeWindow, threadCount, maxPosts, scrapers):
	locations = getLinesInFile(filePath)
	scrapeLocationsFromList(locations, dirPrefix, date,timeWindow, threadCount, maxPosts, scrapers)

def scrapeCitiesFromList(cityList, dirPrefix, threadCount, scrapers):
	threads = []
	i = 0
	while(True):
		if(threading.active_count() <= threadCount):
			if(i == len(cityList)):
				break
			for s in scrapers:
				if(not s.inUse):
					threads.append(ScrapeThread(target=scrapeCityToFile, args=(dirPrefix, cityList[i], s)))
					threads[-1].start()
					i += 1
					break
		time.sleep(0.5)

	for t in threads:
		t.join()

def scrapeLocationsFromList(locList, dirPrefixes, date, timeWindow, threadCount, maxPosts, scrapers):
	threads = []
	i = 0
	while(True):
		if(threading.active_count() <= threadCount):
			if(i == len(locList)):
				break
			for s in scrapers:
				if(not s.inUse):
					threads.append(ScrapeThread(target=scrapeLocationToFile, args=(dirPrefixes[i], locList[i], date, timeWindow, maxPosts, s)))
					threads[-1].start()
					i += 1
					break
		time.sleep(0.5)

	for t in threads:
		t.join()

def scrapeLocationsFromFolder(dirString, suffix, dirPrefix, date, timeWindow, threadCount, maxPosts, scrapers):
	directory = os.fsencode(dirString)
	locations = []
	targetDirs = []
	for file in os.listdir(directory):
		fileName = os.fsdecode(file)
		if(fileName.endswith(suffix)):
			print("getting locations in " + fileName)
			filePath = dirString + fileName
			for line in getLinesInFile(filePath):
				locations.append(line)
				targetDirs.append(dirPrefix + fileName.replace(suffix, "")) #remove ending

	scrapeLocationsFromList(locations, targetDirs, date, timeWindow, threadCount, maxPosts, scrapers)


class ScrapeThread(threading.Thread):
	def __init__(self, target, args):
		threading.Thread.__init__(self)
		self.target = target
		self.args = args
		self.scraper = args[-1]
		self.scraper.inUse = True

	def run(self):
		try:
			self.target(*self.args)
			self.scraper.driver.get("about:blank")
			self.scraper.inUse = False
		except:
			print("\nException in: " + self.name + ", " + self.args[1])
			traceback.print_exc()
			print("")
			self.scraper.inUse = False

class ScraperStarterThread(threading.Thread):
	def __init__(self, profilePath, driverPath,scrapers):
		threading.Thread.__init__(self)
		self.profilePath = profilePath
		self.driverPath = driverPath
		self.scrapers = scrapers

	def run(self):
		print("starting " + self.profilePath)
		self.scrapers.append(LocationScraper(self.profilePath, self.driverPath))

def main():
	#   Arguments  #
	parser = argparse.ArgumentParser(description="Instagram Location Scraper")
	parser.add_argument("-d", "--date", type=str, default="now", help="Date up till which to scrape, eg. 2017-06-01T10:00:00")
	parser.add_argument("-l", "--location", type=str, default="no", help="Location Number to scrape, eg. 214335386/ for Englischer Garten")
	parser.add_argument("-t", "--timeWindow", type=float, default=1.0, help="Timeframe to check number of posts in hours, eg. 1.0")
	parser.add_argument("-c", "--city", type=str, default="no", help="City to scrape location links from, eg. c579270/ for Munich")
	parser.add_argument("-dir", "--dirPrefix", type=str, default="./data/", help="directory to save results, default: ./data/")
	parser.add_argument("-fromFile", default=("no", "no"), nargs=2, help="File containing a list of locations/cities to scrape, specify with c or l, eg. -list cities.txt c")
	parser.add_argument("-threads", "--threadCount", type=int, default=1, help="how many threads to use")
	parser.add_argument("-fromDir", type=str, default=("no", "no"), nargs=2, help="Directory containing files with lists of locations to scrape with suffix to specify which files to scrape, eg. -lDir ./data/Locations _Locations.txt")
	parser.add_argument("-max", "--maxPosts", type=int, default=-1, help="maximum number of posts to scrape, eg. due to performance reasons")
	parser.add_argument("-drv", "--driverPath", type=str, default=CHROMEDRIVER_PATH, help=("path to chromedriver, default = " + CHROMEDRIVER_PATH))

	args = parser.parse_args()
	#  End Argparse #

	scrapers = []
	threads = []
	for i in range(args.threadCount):
		threads.append(ScraperStarterThread((CHROME_PROFILE_PATH + str(i)), CHROMEDRIVER_PATH, scrapers))
		threads[-1].start()

	start = datetime.now()

	for t in threads:
		t.join()

	if(args.fromDir[0] != "no"):
		dirPath = args.fromDir[0]
		fileSuffix = args.fromDir[1]
		scrapeLocationsFromFolder(dirPath, fileSuffix, args.dirPrefix, args.date, args.timeWindow, args.threadCount, args.maxPosts, scrapers)

	if((args.fromFile[0] != "no") and (args.fromFile[1] != "no")):
		filePath = args.fromFile[0]
		typ = args.fromFile[1]
		if(typ == "c"):
			path = args.dirPrefix
			scrapeCitiesFromFile(filePath, path, args.threadCount, scrapers)
		elif(typ == "l"):
			cityName = filePath.split("/")[-1].replace("_Locations.txt", "") #folder with city name
			dirPath = args.dirPrefix + cityName + "/"
			scrapeLocationsFromFile(filePath, dirPath, args.date, args.timeWindow, args.threadCount, args.maxPosts, scrapers)

	if(args.city != "no"):
		scrapeCityToFile(args.dirPrefix, args.city, scrapers[0])

	if(args.location != "no"):
		scrapeLocationToFile(args.dirPrefix, args.location, args.date, args.timeWindow, args.maxPosts, scrapers[0])

	end = datetime.now()
	print ("scraping time: " + str(end - start))

	if(len(scrapers) > 0):
		for s in scrapers:
			s.quit()

main()