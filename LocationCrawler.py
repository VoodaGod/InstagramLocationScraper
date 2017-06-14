import argparse
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException
from datetime import datetime
from datetime import timedelta
import dateutil.parser
import traceback
import os
import threading


# URLS
HOST = "https://www.instagram.com"
RELATIVE_URL_LOCATION = "/explore/locations/"

#Element locators
#LOC_LOAD_MORE = (By.CSS_SELECTOR, "a._8imhp._glz1g") #clicking on last post automatically loads more
LOC_DATE = (By.CSS_SELECTOR, "time")
LOC_CLOSE_BUTTON = (By.CLASS_NAME, "_3eajp")
LOC_SEE_MORE = (By.CLASS_NAME, "_jn623")
LOC_EMAIL_BANNER = (By.CLASS_NAME, "_8yoiv")

#Class names
CLASS_LOCATION_LINK = "_3hq20"
CLASS_POST = "_ovg3g"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"

#path for the scraper profile
CHROME_PROFILE_PATH = "./Scraper"
CHROMEDRIVER_PATH = "./chromedriver.exe"

MAX_WAIT = 7
TIMEOUT_MINUTES = 20
ERROR_INDICATOR = -9999

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
		self.bannerClosed = False #email banner only needs to be closed on first load
		self.timeLimit  = datetime.now() + timedelta(minutes=TIMEOUT_MINUTES)

	def quit(self):
		"""quit the driver"""
		self.driver.quit()

	class PageNotFoundException(Exception):
		"""raise when Instagram can't find a post"""

	def scrapeLocation(self, location, dateTo, dateFrom, maxPosts):
		"""return number of posts at location since dateFrom till dateTo, scrolling at most to maxPosts"""
		self.timeLimit = datetime.now() + timedelta(minutes=TIMEOUT_MINUTES)
		attempts = 0
		while(attempts < 3): #have to restart scrape if clicked on deleted post
			if(attempts > 0):
				print("\nrestarting scrape of " + location + ", attempt " + str(attempts) + "\n")
			try:
				self.browseLocationPage(location)
				try:
					postList = self.scrollToDate(dateFrom, maxPosts)
					if(len(postList) <= 9): #no recent posts, only "top posts" or none
						return 0
					firstPostIndex = self.findFirstPost(dateFrom, postList)
					lastPostIndex = self.findLastPost(dateTo, postList, firstPostIndex)
				except TimeoutException:
					print("scraper " + location + " timed out")
					return ERROR_INDICATOR
				if(len(postList) == (maxPosts + 9)): #didn't finish scrolling
					return -(firstPostIndex - lastPostIndex) #negative = more than
				else:
					return (firstPostIndex - lastPostIndex)
			except self.PageNotFoundException:
				attempts += 1


	def scrapeCity(self, city):
		"""return list of relative urls of all locations in a city"""
		self.browseLocationPage(city)
		while(True):
			self.driver.execute_script(SCROLL_DOWN)
			time.sleep(0.2)
			if(not self.clickElement(locator=LOC_SEE_MORE)):
				break
			time.sleep(1) #seems to get duplicate elements when looping too fast

		locationLinks = []
		for element in self.driver.find_elements_by_class_name(CLASS_LOCATION_LINK):
			locationLinks.append(element.get_attribute("href").replace(HOST + RELATIVE_URL_LOCATION, ""))
		return locationLinks

	def browseLocationPage(self, location):
		"""browses a page with partial url relative to location url"""
		targetURL = HOST + RELATIVE_URL_LOCATION + location
		self.driver.get(targetURL)
		while(self.driver.current_url != targetURL):
			print("retry getting " + targetURL)
			time.sleep(0.5)
			self.driver.get(targetURL)

	def clickElement(self, locator=(), element=None):
		"""returns True if successfully clicked an element by locator or reference"""
		waitAfterClick = 0.2
		el = None
		try: #click normally
			if(locator != ()): #by locator
				try: #try finding & clicking it
					el = WebDriverWait(self.driver, MAX_WAIT).until(EC.presence_of_element_located(locator))
					el.click() #raises WebDriverException if element not clickable
					time.sleep(waitAfterClick)
					return True
				except TimeoutException: #not found
					return False
			elif(element != None): #by element
				el = element
				try: #if element is on page, try to click it
					try:#check if element is on current page
						WebDriverWait(self.driver, MAX_WAIT).until_not(EC.staleness_of(element))
					except TimeoutException: #if it's not
						return False
					el.click() #raises WebDriverException if element not clickable
					time.sleep(waitAfterClick)
					return True
				except StaleElementReferenceException:
					return False
				except WebDriverException: #handle below
					raise
			return False #nothing to click

		except WebDriverException: #element wasn't clickable, try sending enter instead
			try:
				if(el == None):
					return False
				actions = webdriver.ActionChains(self.driver).send_keys_to_element(el, Keys.ENTER)
				actions.move_to_element(el)
				actions.perform()
				time.sleep(waitAfterClick)
				return True
			except (StaleElementReferenceException, WebDriverException): #element not on current page
				return False


	def scrollToDate(self, dateFrom, maxPosts):
		"returns list of posts since dateFrom, scrolling at most to maxPosts"
		self.driver.execute_script(SCROLL_DOWN)
		prevLength = 0
		scrollCounter = 0
		while(datetime.now() < self.timeLimit):
			if(not self.bannerClosed): #only need to close banner once
				self.bannerClosed = self.clickElement(locator=LOC_EMAIL_BANNER)

			postList = self.driver.find_elements_by_class_name(CLASS_POST)
			if(len(postList) < 9):
				return [] #no recent posts, only "top posts" or none
			if(not (len(postList) > prevLength)): #no new posts loaded yet
				self.driver.execute_script(SCROLL_DOWN)
				scrollCounter += 1
				time.sleep(0.3)
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

			#check if last post is older than dateFrom, then return postList
			if(not self.clickElement(element=postList[-1])):
				if(not self.clickElement(locator=LOC_CLOSE_BUTTON)):
					if(self.driver.title == "Page Not Found • Instagram"):
						raise self.PageNotFoundException #post was deleted
				continue #clicked close button, try clicking post again
			try:
				dateElement = WebDriverWait(self.driver, MAX_WAIT).until(EC.presence_of_element_located(LOC_DATE))
			except TimeoutException:
				continue
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			self.clickElement(locator=LOC_CLOSE_BUTTON)
			if(date <= dateFrom): #post is older than dateFrom
				return postList
			self.driver.execute_script(SCROLL_DOWN)

		print("scrolling timed out at: " + self.driver.current_url)
		raise TimeoutException

	def binaryDateSearch(self, dateCmp, postList, left, right):
		"""return index for dateCmp in postList between left & right"""
		while(datetime.now() < self.timeLimit):
			middle = int((left + right) / 2)
			if(not self.clickElement(element=postList[middle])):
				if(not self.clickElement(locator=LOC_CLOSE_BUTTON)):
					if(self.driver.title == "Page Not Found • Instagram"):
						raise self.PageNotFoundException
				continue #clicked close button, try clicking post again
			try:
				dateElement = WebDriverWait(self.driver, MAX_WAIT).until(EC.presence_of_element_located(LOC_DATE))
			except TimeoutException:
				continue
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			self.clickElement(locator=LOC_CLOSE_BUTTON)
			if(date == dateCmp):
				return middle
			elif(date > dateCmp):
				left = middle + 1
			elif(date < dateCmp):
				right = middle - 1
			if(right < left): #not sure why return left seems to work
				return left

		print("search timed out at: " + self.driver.current_url)
		raise TimeoutException

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
	"""scrapes locations at relative city url to a file in dirPrefix"""
	path = dirPrefix + "Locations/" + city.replace("/","_") + "Locations.txt"
	print("scraping city: " + city + " for locations to " + path)
	locations = scraper.scrapeCity(city)
	#write to file
	os.makedirs(os.path.dirname(path), exist_ok=True)
	file = open(path, "w")
	for loc in locations:
		file.write(loc+ "\n")
	file.close()

def scrapeLocationToFile(dirPrefix, location, date, timeWindow, maxPosts, scraper):
	"""scrapes postcount of location in timeWindow before date, scrolling to a maximum of maxPosts, date needs to be parseable by dateutil, e.g 2017-06-09T20:00:00"""
	#parse dates
	if(date == "now"):
		dateTo = datetime.utcnow()
	else:
		dateTo = dateutil.parser.parse(date, ignoretz=True)
	dateFrom = dateTo - timedelta(hours=timeWindow)
	if(dateTo > datetime.utcnow()):
		print("waiting until " + dateTo.isoformat())
		while(dateTo > datetime.utcnow()): #wait until date has passed
			time.sleep(1)

	#scrape & write to file
	path = dirPrefix + "_Postcounts/" + location.replace("/","_") + "Postcounts.txt" #which file to write to
	print("Scraping location " + location + " for number of pictures posted between " + str(dateFrom) + " and " + str(dateTo) + " to " + path)
	numPosts = scraper.scrapeLocation(location, dateTo, dateFrom, maxPosts)
	print(location + ": " + str(numPosts))
	os.makedirs(os.path.dirname(path), exist_ok=True)
	file = open(path, "a+")
	file.write(dateTo.isoformat() + "\t" + str(numPosts) + "\n")
	file.close()

def getLinesInFile(filePath):
	"""returns list of lines in file at filePath"""
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
	"""scrapes all locations in cities in file at filePath, saves to dirPrefix, spawns threadCount threads"""
	cities = getLinesInFile(filePath)
	scrapeCitiesFromList(cities, dirPrefix, threadCount, scrapers)

def scrapeLocationsFromFile(filePath, dirPrefix, date, timeWindow, threadCount, maxPosts, scrapers):
	"""scrapes postcounts from locations in file at filePath in timeWindow before date, saves them to dirPrefix,spawns threadCount threads, and scrolls to maximum of maxPosts posts"""
	locations = getLinesInFile(filePath)
	scrapeLocationsFromList(locations, dirPrefix, date,timeWindow, threadCount, maxPosts, scrapers)

def scrapeCitiesFromList(cityList, dirPrefix, threadCount, scrapers):
	"""scrapes locations in cities in cityList to file in dirPrefix, spawns threadCount threads"""
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
		time.sleep(1)

	for t in threads:
		t.join()

def scrapeLocationsFromList(locList, dirPrefixes, date, timeWindow, threadCount, maxPosts, scrapers):
	"""scrapes postscounts at locations in locList in timeWindow before date, spawning threadCount threads, scrolling to maximum of maxPosts"""
	threads = []
	i = 0
	while(True):
		#start a new thread if fewer than threadCount active
		if(threading.active_count() <= threadCount):
			if(i == len(locList)): #don't start more threads than locations
				break
			for s in scrapers: #find a free scraper
				if(not s.inUse):
					threads.append(ScrapeThread(target=scrapeLocationToFile, args=(dirPrefixes[i], locList[i], date, timeWindow, maxPosts, s)))
					threads[-1].start()
					i += 1
					break
		time.sleep(1)

	#once all threads started, wait for them to finish
	for t in threads:
		t.join()

def scrapeLocationsFromFolder(dirString, suffix, dirPrefix, date, timeWindow, threadCount, maxPosts, scrapers):
	"""scrape postcounts at locations listed in files having suffix in dirString in timeWindow before date to dirPrefix, spawning threadCount threads, scrolling to maximum of maxPosts"""
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
	"""runs scraping function target(args) in own scraper instance"""
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
		except KeyboardInterrupt:
			pass
		except:
			print("\nException in: " + self.name + ", " + self.args[1])
			traceback.print_exc()
			print("")
		finally:
			self.scraper.inUse = False #scraper can be used by next thread

class ScraperStarterThread(threading.Thread):
	"""starts scraper instance with profile at profilePath and driver at driverPath"""
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
	parser.add_argument("-l", "--location", type=str, default="no", help="Location Number to scrape, eg. 214335386/ for Englischer Garten")
	parser.add_argument("-c", "--city", type=str, default="no", help="City to scrape location links from, eg. c579270/ for Munich")
	parser.add_argument("-fromFile", default=("no", "no"), nargs=2, metavar=("FILE", "TYPE"), help="File containing a list of locations/cities to scrape, specify with c or l, eg. -list cities.txt c")
	parser.add_argument("-fromDir", type=str, default=("no", "no"), nargs=2, metavar=("DIR", "SUFFIX"), help="Directory containing files with lists of locations to scrape with suffix to specify which files to scrape, eg. -lDir ./data/Locations _Locations.txt")
	parser.add_argument("-d", "--date", type=str, default="now", help="Date up till which to scrape, eg. 2017-06-01T10:00:00")
	parser.add_argument("-t", "--timeWindow", type=float, default=1.0, help="Timeframe to check number of posts in hours, eg. 1.0")
	parser.add_argument("-dir", "--dirPrefix", type=str, default="./data/", help="directory to save results to, default: ./data/")
	parser.add_argument("-threads", "--threadCount", type=int, default=1, help="how many threads to use")
	parser.add_argument("-max", "--maxPosts", type=int, default=-1, help="maximum number of posts to scrape, eg. due to performance reasons")
	parser.add_argument("-drv", "--driverPath", type=str, default=CHROMEDRIVER_PATH, help=("path to chromedriver, default = " + CHROMEDRIVER_PATH))
	parser.add_argument("-drvProfile", "--driverProfilePrefix", type=str, default=CHROME_PROFILE_PATH, help="prefix for scraper chrome profiles, default = " + CHROME_PROFILE_PATH)

	args = parser.parse_args()
	#  End Argparse #

	scrapers = []
	try:
 		#wait until dateTo reached
		if(args.date != "now"):
			dateTo = dateutil.parser.parse(args.date)
			print("waiting until " + dateTo.isoformat())
			while(dateTo > datetime.utcnow()):
				time.sleep(1)

		threads = []
		#start scrapers concurrently
		for i in range(args.threadCount):
			threads.append(ScraperStarterThread((args.driverProfilePrefix + str(i)), args.driverPath, scrapers))
			threads[-1].start()

		#wait for all scrapers to finish starting
		for t in threads:
			t.join()

		#for printing duration of scraping
		start = datetime.now()

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
		print ("scraping time: " + str(end - start) + "\n")

	except KeyboardInterrupt:
		pass
	finally:
		if(len(scrapers) > 0): #for some reason does not work with keyboardInterrupt
			for s in scrapers:
				s.quit()

main()