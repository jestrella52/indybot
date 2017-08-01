#!/usr/bin/env python

import re
import sys
import time
import django
import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By

from slackclient import SlackClient

#
# Slack Initialization
#
BOT_ID = "U1B41SSLR"
BOT_TOKEN = "xoxb-45137910705-xkRY9dxy9j79Pf7izR3LkzHa"
AT_BOT = "<@" + BOT_ID + ">"
slack_client = SlackClient(BOT_TOKEN)

#
# Selenium Initialiazation
#
driver = webdriver.PhantomJS()
driver.set_page_load_timeout(30)
pageLoaded = False

url="http://racecontrol.indycar.com"

while not pageLoaded:
    print "Getting URL..."
    try:
        driver.get(url)
        pageLoaded = True
    except:
        print "Timeout.  Retrying."
        time.sleep(3)

print "Loaded Page."
# print driver.page_source

trackHot = False

# Set to True to ignore what series is on track.
seriesBypass = False

# while trackActive == False:
#     # Check to see if the "No Track Activity" DIV is visible.  If so, we're done.
#     trackActDivStyle = driver.find_elements_by_xpath("//div[@id='NoActivityDiv']")[0].get_attribute('style')
#     if re.search('block', trackActDivStyle) or seriesBypass:
#         print "NO TRACK ACTIVITY."
#     else:
#         trackActive = True

while trackHot == False:
    seriesHeaderDivStyle = driver.find_elements_by_xpath("//div[@id='SeriesHeaderImage']")[0].get_attribute('style')
    if re.search('indycar', seriesHeaderDivStyle):
        trackHot = True
    else:
        print "IndyCar not on track."
        time.sleep(15)

# IndyCar is on the track
print "INDYCAR on track!"
if slack_client.rtm_connect():
    print "Connected to Slack."
    #slack_client.api_call("chat.postMessage", channel="indybot-dev", text="Startup successful!", as_user=True)

currentFlag = "green"

raceInProgress = True
flagUpdateCounter = 0

while raceInProgress:

    try:
        flagDivStyle = driver.find_elements_by_xpath("//div[@id='HeaderDiv']")[0].get_attribute('style')
        flagMatches = re.search('img_flag_(\w+)\.jpg', flagDivStyle)
    except:
        time.sleep(3)
        continue

    try:
        lapLabel = driver.find_elements_by_xpath("//label[@id='LapsLabel']")[0]
        lapMatches = re.search('Lap (\d+) of (\d+)', lapLabel.get_property('text'))
        currentLap = lapMatches.group(1)
        lastLap = lapMatches.group(2)
    except:
        time.sleep(1)

    try:
        tableContainer = driver.find_elements_by_xpath("//div[@class='container']/div[4]/div")
        leader = tableContainer[1].get_property('text')
    except:
        time.sleep(1)

    try:
        newFlag = flagMatches.group(1)
        if newFlag != currentFlag:
            flagUpdateCounter = 0
            print "NEW FLAG: " + newFlag
            currentFlag = newFlag
            if newFlag == "green":
                message = "Green, green, _GREEN_!"
            elif newFlag == "yellow":
                message = "*YELLOW, YELLOW, YELLOW!*"
            elif newFlag == "white":
                message = "White flag! One to go for the leader!"
            elif newFlag == "checker":
                message = "Checkered flag!"
                raceInProgress = False
            slack_client.api_call("chat.postMessage", channel="moderators", text=message, as_user=True)
        else:
            flagUpdateCounter = flagUpdateCounter + 1
            # if flagUpdateCounter == 50:
            if flagUpdateCounter == 10:
                print "[" + str(currentLap) + "/" + str(lastLap) + "] - " + currentFlag.title() + " - " + leader
                flagUpdateCounter = 0

        time.sleep(3)

    except KeyboardInterrupt:
        print "BREAK!  Exiting."
        driver.quit()
        sys.exit(1)
    except:
        print "Waiting for race to start..."
        time.sleep(10)

driver.quit()

# userAgent = {'User-agent': 'Mozilla/5.0 (Windows NT 5.1; rv:32.0) Gecko/20100101 Firefox/31.0'}
# flagXPath = '//div[@id="TimingScoringTable"]//@style'
# seriesXPath = '//div[@id="SeriesHeaderImage"]//@style'
# page = requests.get("http://racecontrol.indycar.com/", headers=userAgent)
#
# outfile = open("debug.html", "w")
# outfile.write(page.content)
# outfile.close()
#
# tree = html.fromstring(page.content)
# shi = tree.xpath(seriesXPath)
# flag = tree.xpath(flagXPath)
#
# for atag in flag:
#     print atag
