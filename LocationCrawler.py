import argparse
from sys import platform
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime
from datetime import timedelta
import dateutil.parser
import traceback
import os



# URLS
HOST = "https://www.instagram.com"
RELATIVE_URL_LOCATION = "/explore/locations/"

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
CHROME_PROFILE_PATH = ".\Scraper"

class LocationScraper(object):
	def __init__(self):
		options = webdriver.ChromeOptions()
		options.add_argument("user-data-dir=" + CHROME_PROFILE_PATH)

		if platform == "win32":
			self.driver = webdriver.Chrome(executable_path = "./chromedriverWIN.exe", chrome_options = options)
		elif platform == "darwin":
			self.driver = webdriver.Chrome(executable_path = "./chromedriverMAC", chrome_options=options)
		else:
			print("neither Windows nor Mac detected")

	def quit(self):
		self.driver.quit()

	def scrape(self, location, dateTo, dateFrom):
		self.browseTargetPage(location)
		postList = self.scrollToDate(dateFrom)
		firstPostIndex = self.findFirstPost(dateFrom, postList)
		lastPostIndex = self.findLastPost(dateTo, postList)
		return (firstPostIndex - lastPostIndex)

	def browseTargetPage(self, location):
		targetURL = HOST + RELATIVE_URL_LOCATION + location
		self.driver.get(targetURL)

	#scrolls until an imager older than dateFrom is found
	def scrollToDate(self, dateFrom):
		self.driver.execute_script(SCROLL_DOWN)
		try:
			loadmore = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_LOAD_MORE)))
		except:
			pass
		else:
			loadmore.click()
		while(True):
			postList = self.driver.find_elements_by_class_name(POST)
			postList[-1].click()
			dateElement = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_DATE)))
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			self.driver.find_element_by_class_name(CLOSE_BUTTON).click()
			if(date <= dateFrom):
				return postList
			self.driver.execute_script(SCROLL_DOWN)
			time.sleep(0.1)

	def findFirstPost(self, dateFrom, postList):
		for i in range(1, len(postList)): #start looking from the back
			postList[-i].click()
			dateElement = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_DATE)))
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			self.driver.find_element_by_class_name(CLOSE_BUTTON).click()
			if (date >= dateFrom):
				return len(postList) - i
		return 9 #no posts since dateFrom, return first post in "most recent"

	def findLastPost(self, dateTo, postList):
		for i in range(9, len(postList)): #first 9 posts are "Top Posts"
			postList[i].click()
			dateElement = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_DATE)))
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			self.driver.find_element_by_class_name(CLOSE_BUTTON).click()
			if (date <= dateTo):
				return i #return first post from before dateTo

	def getLocations(self, city):
		self.browseTargetPage(city)
		while(True):
			try:
				seeMore = WebDriverWait(self.driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, SEE_MORE)))
			except:
				break
			self.driver.execute_script(SCROLL_DOWN)
			time.sleep(0.75)
			try:
				seeMore.click()
			except:
				pass
		locationLinks = []
		for element in self.driver.find_elements_by_class_name(LOCATION_LINK):
			locationLinks.append(element.get_attribute("href").replace(HOST + RELATIVE_URL_LOCATION, ""))
		return locationLinks




def main():
	#   Arguments  #
	parser = argparse.ArgumentParser(description="Instagram Location Scraper")
	#parser.add_argument("-df", "--dateFrom", type=str, default="now - 1h", help="Date from which to scrape")
	parser.add_argument("-d", "--date", type=str, default="now", help="Date up till which to scrape, eg. 2017-06-01T10:00:00")
	parser.add_argument("-l", "--location", type=str, default="no", help="Location Number to scrape, eg. 214335386 for Englischer Garten")
	parser.add_argument("-t", "--timeWindow", type=float, default=1.0, help="Timeframe to check number of posts in hours, eg. 1.0")
	parser.add_argument("-c", "--city", type=str, default="no", help="City to scrape location links from, eg c579270 for Munich")
	parser.add_argument("-dir", "--dirPrefix", type=str, default="./data/", help="directory to save results, default: ./data/")


	args = parser.parse_args()
	#  End Argparse #

	if(args.date == "now"):
		dateTo = datetime.utcnow()
	else:
		dateTo = dateutil.parser.parse(args.date, ignoretz=True)
	dateFrom = dateTo - timedelta(hours=args.timeWindow)

	scraper = LocationScraper()
	try:
		if(args.city != "no"):
			path = args.dirPrefix + "Locations/" + args.city.replace("/","_") + "Locations.txt"
			print("scraping city: " + args.city + " for locations to " + path)
			locations = scraper.getLocations(args.city)
			os.makedirs(os.path.dirname(path), exist_ok=True)
			file = open(path, "w")
			for loc in locations:
				file.write(loc+ "\n")
			file.close()

		if(args.location != "no"):
			path = args.dirPrefix + "Postcounts/" + args.location.replace("/","_") + "Postcounts.txt"
			print("Scraping location " + args.location + " for number of pictures posted between " + str(dateFrom) + " and " + str(dateTo) + " to " + path)
			numPosts = scraper.scrape(location=args.location, dateTo=dateTo, dateFrom=dateFrom)
			print(str(numPosts))
			os.makedirs(os.path.dirname(path), exist_ok=True)
			file = open(path, "a+")
			file.write(dateTo.isoformat() + "\t" + str(numPosts) + "\n")
			file.close()

	except:
		traceback.print_exc()

	scraper.quit()

main()