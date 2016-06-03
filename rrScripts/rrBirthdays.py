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

query = "SELECT * from driver where dob IS NULL"
cur.execute(query)
drivers = cur.fetchall()

bornPattern = re.compile('^<BR><BR><B>Born:</B>\s?([a-zA-Z]+)\s+(\d+),\s(\d+)') #\s?([a-zA-Z]+)\s(\d+), (\d+)$')


for driver in drivers:
    driverName = string.replace(driver['first'] + " " + string.replace(driver['last'], ' Sr.', ''), ',', '')
    driverAddr = "http://racing-reference.info/driver/" + string.replace(driverName, ' ', '_')
    print driverAddr
    page = requests.get(driverAddr)
    html = page.content.split('\n')
    for line in html:
        match = bornPattern.match(line)
        if match:
            print "FOUND"
            print "Month: -" + match.group(1) + '-'
            print "Day:   -" + match.group(2) + '-'
            print "Year:  -" + match.group(3) + '-'
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

    time.sleep(5)
