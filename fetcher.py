from bs4 import BeautifulSoup
import requests
import copy
import re
import logging 

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MENU_URL = "http://www.colby.edu/diningservices/menus/"

def getMenuByDate(date):
	# insert correct code here later
	return getMenuFromUrl(MENU_URL)


def getMenuFromUrl(url):
	print "Getting raw menu data ..."
	r = requests.get(url)
	rawData = r.text

	soup = BeautifulSoup(rawData)
	# we need another one because of some weird behaviour in bs
	# where when .append() is called it actually move the element
	soup2 = BeautifulSoup(rawData)

	menusByMeals = processMealMenus(soup)
	menusByDiningHalls = processDiningHallMenus(soup2)
	
	# the name is a little misleading ...
	menusByMeals.update(menusByDiningHalls)
	return menusByMeals

def processMealMenus(rawMenu):
	(rawBreakfastHtml, rawLunchHtml, rawDinnerHtml) = seperateByMeals(rawMenu)
	
	cleanBreakfastHtml = cleanUpRawMenuHtml(rawBreakfastHtml)
	cleanLunchHtml = cleanUpRawMenuHtml(rawLunchHtml)
	cleanDinnerHtml = cleanUpRawMenuHtml(rawDinnerHtml)
	
	titledBreakfastMenu = addMenuTitle(cleanBreakfastHtml, "Breakfast")
	titledLunchMenu = addMenuTitle(cleanLunchHtml, "Lunch")
	titledDinnerMenu = addMenuTitle(cleanDinnerHtml, "Dinner")

	menus = {}
	menus['breakfast'] = innerHTML(titledBreakfastMenu)
	menus['lunch'] = innerHTML(titledLunchMenu)
	menus['dinner'] = innerHTML(titledDinnerMenu)

	return menus

def addMenuTitle(menu, title):
	menuWithTitle = BeautifulSoup()
	menuWithTitle.append(BeautifulSoup("<div class='menuTitle'>" + title + "</div>"))
	menuWithTitle.append(menu)
	return menuWithTitle

def cleanUpRawMenuHtml(rawHtmlSoup):
	logger.info("Cleaning up raw html ...")
	logger.info("---> Removing nutritional information links... Who read those?")
	
	for link in rawHtmlSoup.findAll("a", "nutrition fancybox.iframe"):
		link.extract()

	logger.info("---> Replace some strange, alient tags with normal ones...")
	
	for addressTag in rawHtmlSoup.findAll("address"):
		addressTag.name = "p"

	logger.info("---> Replace the dietary codes hrefs, they are fucking useles... ")
	for link in rawHtmlSoup.findAll("a", {"data-toggle":"tooltip"}):
		link.name = "span"
		del(link["href"])
		del(link["data-toggle"])
		if 'GF' in link.text: 
			link["class"] = "glutenFree"
		elif 'V' in link.text: 
			link["class"] = "vegetarian"
		elif 'P' in link.text: 
			link["class"] = "containsPork"
	return rawHtmlSoup


def seperateByMeals(rawMenu):
	rawBreakfastHtml = rawMenu.find("div", {"id":"breakfast"})
	rawLunchHtml = rawMenu.find("div", {"id":"lunch"})
	rawDinnerHtml = rawMenu.find("div", {"id":"dinner"})

	return (rawBreakfastHtml, rawLunchHtml, rawDinnerHtml)


def processDiningHallMenus(rawMenu):
	(rawBreakfastHtml, rawLunchHtml, rawDinnerHtml) = seperateByMeals(rawMenu)

	menus = {}

	cleanBreakfastHtml = cleanUpRawMenuHtml(rawBreakfastHtml)
	cleanLunchHtml = cleanUpRawMenuHtml(rawLunchHtml)
	cleanDinnerHtml = cleanUpRawMenuHtml(rawDinnerHtml)
	
	breakfastByDiningHalls = seperateByDiningHalls(cleanBreakfastHtml, "Breakfast ")
	lunchByDiningHalls = seperateByDiningHalls(cleanLunchHtml, "Lunch ")
	dinnerByDiningHalls = seperateByDiningHalls(cleanDinnerHtml, "Dinner ")
	
	fossMenu = BeautifulSoup()
	bobsMenu = BeautifulSoup()
	danaMenu = BeautifulSoup()
	spaMenu = BeautifulSoup()
	take4Menu = BeautifulSoup()

	for seperatedMenu in (breakfastByDiningHalls, lunchByDiningHalls, dinnerByDiningHalls):
		fossMenu.append(seperatedMenu['foss'])
		bobsMenu.append(seperatedMenu['bobs'])
		danaMenu.append(seperatedMenu['dana'])
		spaMenu.append(seperatedMenu['spa'])
		take4Menu.append(seperatedMenu['take4'])
	
	fossMenu = addMenuTitle(fossMenu, "Foss")
	danaMenu = addMenuTitle(danaMenu, "Dana")
	bobsMenu = addMenuTitle(bobsMenu, "Bobs")
	spaMenu = addMenuTitle(spaMenu, "The Spa")
	take4Menu = addMenuTitle(take4Menu, "Take 4")

	menus['foss'] = innerHTML(fossMenu)
	menus['dana'] = innerHTML(danaMenu)
	menus['bobs'] = innerHTML(bobsMenu)
	menus['spa'] = innerHTML(spaMenu)
	menus['take4'] = innerHTML(take4Menu)
	
	return menus


def seperateByDiningHalls(rawMenuSoup, mealName):
	print "Seperating by dining halls ..."

	# this should give back a list of 4 items, correspond to the 4 columns on the website
	# dana - roberts - foss - [spa/togo]
	menuList = rawMenuSoup.findAll("div", "span3")

	danaMenu = menuList[0]
	bobsMenu = menuList[1]
	fossMenu = menuList[2]
	spaAndTake4Menu = menuList[3]

	print "Seperating spa and take4 menu"
	
	spaMenu = BeautifulSoup()
	take4Menu = BeautifulSoup()

	if len(spaAndTake4Menu.findAll("h3")) > 1:
		print "Found take 4 menu ..."
		take4Header = spaAndTake4Menu.findAll("h3")[1]
		take4HeaderCopy = copy.deepcopy(take4Header)
		while(take4Header != None):
			take4Menu.append(take4Header)
			take4Header = take4Header.nextSibling
		while(take4HeaderCopy != None):
			spaMenu.append(take4HeaderCopy)
			take4HeaderCopy = take4HeaderCopy.previousSibling
	else:
		print "No take 4 menu ..."
		spaMenu = spaAndTake4Menu

	result = {}
	result['dana'] = replaceDiningHallNameWithMealName(danaMenu, 'Dana', mealName)
	result['bobs'] = replaceDiningHallNameWithMealName(bobsMenu, 'Roberts', mealName)
	result['foss'] = replaceDiningHallNameWithMealName(fossMenu, 'Foss', mealName)
	result['spa'] = replaceDiningHallNameWithMealName(spaMenu, 'Spa', mealName)
	result['take4'] = take4Menu

	return result

def replaceDiningHallNameWithMealName(menu, diningHallName, mealName):
	'''
	The raw menu for each dining hall has the dining hall name
	Instead, we want to have the meal name
	'''
	findtoure = menu.findAll(text=re.compile(diningHallName))
	# we should only find 1 instance, if not, something fishy is going on
	if ((findtoure != None) and (len(findtoure) == 1)):
		diningHallText = findtoure[0]
		fixed_text = unicode(diningHallName).replace(diningHallName, mealName)
		diningHallText.replace_with(fixed_text)
	else:
		logger.error("Dining hall name appears more than once. Dining hall name will NOT be replaced with meal name.")
		logger.error("Found occurances: " + str(findtoure))
	return menu

def innerHTML(element):
    return element.decode_contents(formatter="html")

def shittyTest():
	menus = getMenuByDate("foo")
	for menuName, menuContent in menus.iteritems():
		print "========================================" + menuName + "========================================="
		print menuContent

if __name__ == "__main__":
	shittyTest()