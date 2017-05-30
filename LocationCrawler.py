import argparse
import requests
from sys import platform
import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime
from datetime import timedelta
import dateutil.parser



# URLS
HOST = "http://www.instagram.com"
RELATIVE_URL_LOCATION = "/explore/locations/"

# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = "a._8imhp._glz1g"
CSS_RIGHT_ARROW = "a[class='_de018 coreSpriteRightPaginationArrow']"

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

	def scrape(self, dirPrefix, location, dateFrom, dateTill):
		print("dirPrefix: " + dirPrefix + ", location: " + location + ", dateFrom: " + dateFrom + ", dateTill: " + dateTill)
		self.browseTargetPage(location)
		self.scrollToDate(dateFrom)

		#TODO

		print("enter to exit")
		input()
		self.quit()

	def browseTargetPage(self, location):
		targetURL = HOST + RELATIVE_URL_LOCATION + location
		self.driver.get(targetURL)

	#scrolls until an imager older than dateFrom is found
	def scrollToDate(self, dateFrom):
		if (dateFrom == "now - 1h"):
			dateFrom = datetime.utcnow()
			delta = timedelta(hours=10)
			dateFrom -= delta
		else:
			dateFrom = dateutil.parser.parse(dateFrom, ignoretz=True)

		self.driver.execute_script(SCROLL_DOWN)
		loadmore = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_LOAD_MORE)))
		loadmore.click()
		scrollMore = True
		while(True):
			postList = self.driver.find_elements_by_class_name("_ovg3g")
			postList[-1].click()
			dateElement = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a time")))
			date = dateutil.parser.parse(dateElement.get_attribute("datetime"), ignoretz=True)
			#print(date, dateFrom)
			if(date <= dateFrom):
				break
			self.driver.find_element_by_class_name("_3eajp").click()
			self.driver.execute_script(SCROLL_DOWN)




def main():
	#   Arguments  #
	parser = argparse.ArgumentParser(description="Instagram Location Scraper")
	parser.add_argument("-df", "--dateFrom", type=str, default="now - 1h", help="Date from which to scrape")
	parser.add_argument("-dt", "--dateTill", type=str, default="now", help="Date up till which to scrape")
	parser.add_argument("-l", "--location", type=str, default="214335386", help="Location Number eg. 214335386 for Englischer Garten")
	parser.add_argument("-dir", "--dirPrefix", type=str, default="./data/", help="directory to save results")

	args = parser.parse_args()
	#  End Argparse #

	scraper = LocationScraper()
	scraper.scrape(dirPrefix=args.dirPrefix, location=args.location, dateFrom=args.dateFrom, dateTill=args.dateTill)

main()