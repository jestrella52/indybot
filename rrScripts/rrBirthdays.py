#!/usr/bin/env python

#
#   Adds driver birth dates to database.
#

import MySQLdb
import MySQLdb.cursors
import datetime
import requests
import string
import time
import sys
import re

def findDriverID(driverList, last, first):
    for driver in driverList:
        if driver['last'] == last and driver['first'] == first:
            return driver['id']

con = MySQLdb.connect(read_default_group='indybot', port=3306, db='indybot2', cursorclass=MySQLdb.cursors.DictCursor)
cur = con.cursor()

query = "SELECT * from driver where died IS NULL"
cur.execute(query)
drivers = cur.fetchall()

bornPattern = re.compile('^<BR><BR><B>Born:</B>\s?([a-zA-Z]+)\s+(\d+),\s(\d+)') #\s?([a-zA-Z]+)\s(\d+), (\d+)$')
diedPattern = re.compile('.*<B>Died:</B>\s?([a-zA-Z]+)\s+(\d+),\s(\d+)')

for driver in drivers:
    driverName = string.replace(driver['first'] + " " + string.replace(driver['last'], ' Sr.', ''), ',', '')
    # driverName = "Justin Wilson"
    driverAddr = "http://racing-reference.info/driver/" + string.replace(driverName, ' ', '_')
    print driverAddr
    page = requests.get(driverAddr)
    html = page.content.split('\n')
    for line in html:
        match = bornPattern.match(line)
        if match:
            print "BORN: " + match.group(1) + " " + match.group(2) + ", " + match.group(3)
            if int(match.group(3)) == 2016:
                print "ERROR!  YEAR IS THIS YEAR - DRIVER ID: " + str(driver['id'])
                sys.exit()
            stamp = datetime.datetime.strptime(match.group(1) + " " + match.group(2) + ", " + match.group(3), "%B %d, %Y")
            datestamp = stamp.strftime("%Y-%m-%d")
            query = 'UPDATE driver SET dob="'
            query += datestamp
            query += '" where driver.id='
            query += str(driver['id'])
            cur.execute(query)
            con.commit()

        match2 = diedPattern.match(line)
        if match2:
            print "DIED: " + match2.group(1) + " " + match2.group(2) + ", " + match2.group(3)
            if int(match2.group(3)) == 2016:
                print "ERROR!  YEAR IS THIS YEAR - DRIVER ID: " + str(driver['id'])
                sys.exit()
            stamp2 = datetime.datetime.strptime(match2.group(1) + " " + match2.group(2) + ", " + match2.group(3), "%B %d, %Y")
            datestamp2 = stamp2.strftime("%Y-%m-%d")
            query = 'UPDATE driver SET died="'
            query += datestamp2
            query += '" where driver.id='
            query += str(driver['id'])
            cur.execute(query)
            con.commit()
            
    time.sleep(2)
