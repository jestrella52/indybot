#!/usr/bin/env python

import MySQLdb
import MySQLdb.cursors
import datetime
import pycurl
import getopt
import mmap
import sys
import re

class Page:
    def __init__(self):
        self.contents = ''

    def body_callback(self, buf):
        self.contents = self.contents + buf

def findDriverID(driverList, last, first):
    for driver in driverList:
        if driver['last'] == last and driver['first'] == first:
            return driver['id']

raceOpt = False
debug = False
dbWrite = True

try:
    opts, args = getopt.getopt(sys.argv[1:], "dr:x", ["debug", "race=", "nodb"])
except getopt.GetoptError as err:
    print(err)
    sys.exit(2)

for o, a in opts:
    if o == "-d":
        debug = True
    elif o == "-x":
        dbWrite = False
    elif o == "-r":
        raceOpt = a

if not raceOpt:
    print "Specify race id with -r"
    sys.exit(1)

user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36")

con = MySQLdb.connect(read_default_group='indybot', port=3306, db='indybot2', cursorclass=MySQLdb.cursors.DictCursor)
cur = con.cursor()

query = "SELECT * from driver"
cur.execute(query)
drivers = cur.fetchall()

query = "SELECT * from race where id = " + raceOpt
cur.execute(query)
# datePattern = re.compile('^<BR><B><A HREF=/alldates/0407 TITLE="Click here to see all races run on this date">([a-zA-Z0-9\,\s]+)</A></B>')
# lapsPattern = re.compile('^<BR>(\d+) laps')
# lengthPattern = re.compile('^<B>Time of race:</B>\ ([\d:]+)')
# speedAvgPattern = re.compile('<BR><B>Average Speed:</B> ([\d\.]+) mph')
# speedPolePattern = re.compile('<BR><B>Pole Speed:</B> ([\d\.]+) mph')
# cautionsPattern = re.compile('<B>Cautions:</B> (\d+) for (\d+) laps')
# marginPattern = re.compile('<BR><B>Margin of Victory:</B> ([\d+\.]+) sec')
# leadsPattern = re.compile('<BR><B>Lead changes:</B> (\d+)')

resultPattern = re.compile('^<TR .*><TD .*>(\d+)</TD><TD .*>\s?(\d+)</TD><TD .*><A HREF=.*>\s?(\d+)</A></TD><TD class=col><IMG .*> &nbsp; <A HREF=/driver/[a-zA-Z\.\-\,_]+>([a-zA-Z\.\-]+) ([a-zA-Z\.\-\'\s]+)</A>')
flagPattern = re.compile('^<TR .*><TD .*><IMG SRC=/images/(\w+)_flag.png.*></TD><TD .*>(\d+)</TD><TD .*>(\d+)</TD><TD .*>(\d+)</TD><TD class=col>(.*)</TD><TD class=col>&nbsp;</TD></TR>')

for race in cur.fetchall():
    length = 0
    laps = 0
    speedAvg = 0.0
    speedPole = 0.0
    cautions = 0
    cautionLaps = 0
    margin = -1
    leadChanges = 0

    url = race['urlrr']
    c = pycurl.Curl()
    page = Page()
    c.setopt(pycurl.URL, url)
    c.setopt(c.WRITEFUNCTION, page.body_callback)
    c.perform()
    c.close()
    lines = page.contents.split('\n')

    ddb = []

    for line in lines:

        match = flagPattern.match(line)
        if match:
            if match.group(1) != "green":
                startLap    = match.group(2)
                endLap      = match.group(3)
                reason      = match.group(5).replace('&nbsp;', '').strip()
                numPattern = re.compile('\#([\d,]+)')
                numMatch = numPattern.match(reason)
                print numMatch.group(1)
                if numMatch:
                    if len(numMatch.group(1)) > 1:
                        involved = numMatch.group(1).split(',')
                    else:
                        involved = [numMatch.group(1)]
                    for victim in involved:
                        idx = next(index for (index, d) in enumerate(ddb) if d["number"] == victim)
                        print ddb[idx]['last'] + ", " + ddb[idx]['first']
                print match.group(1).ljust(10, ' ') + startLap.rjust(3, ' ') + " - " + endLap.rjust(3, ' ') + " - " + reason


        match = resultPattern.match(line)
        if match:
            finish = match.group(1)
            qual   = match.group(2)
            number = match.group(3)
            first  = match.group(4)
            last   = match.group(5)

            ddbrec = {
                'finish': finish,
                'qual'  : qual,
                'number': number,
                'first' : first,
                'last'  : last
            }
            ddb.append(ddbrec.copy())

            if last == "Pablo Montoya" and first == "Juan":
                first = "Juan Pablo"
                last = "Montoya"
            if last == "Paulo de Oliveira" and first == "Joao":
                first = "Joao Paulo"
                last = "de Oliveira"

            driverID = findDriverID(drivers, last, first)
            if driverID:
                if debug:
                    print "P" + finish.rjust(2, ' ') + " - Q" + qual.rjust(2, ' ') + "  -  " + " #" + str(number).rjust(2, ' ' ) + " - "+ first.ljust(20, ' ') + last.ljust(20, ' ') + "  -  " + str(driverID).rjust(4,' ') + str(race['id']).rjust(4, ' ')
                else:
                    # Qual result
                    query = "SELECT COUNT(*) FROM result WHERE position=" + str(qual) + " AND driver_id=" + str(driverID) + " AND type_id=1 AND race_id=" + str(race['id']) + ";"
                    cur.execute(query)
                    if cur.fetchone()['COUNT(*)'] == 0:
                        print "INSERTING Q RESULT"
                        query = "INSERT INTO result (position, driver_id, type_id, race_id) VALUES (" + str(qual) + ", " + str(driverID) + ", 1, " + str(race['id']) + ");"
                        if dbWrite:
                            cur.execute(query)
                            con.commit()
                    # Finish result
                    query = "SELECT COUNT(*) FROM result WHERE position=" + str(finish) + " AND driver_id=" + str(driverID) + " AND type_id=2 AND race_id=" + str(race['id']) + ";"
                    cur.execute(query)
                    if cur.fetchone()['COUNT(*)'] == 0:
                        print "INSERTING F RESULT"
                        query = "INSERT INTO result (position, driver_id, type_id, race_id) VALUES (" + str(finish) + ", " + str(driverID) + ", 2, " + str(race['id']) + ");"
                        if dbWrite:
                            cur.execute(query)
                            con.commit()
            else:
                print "* * * * * * * * * * [ERROR] * * * * * * * * * *"
                print "P" + finish.rjust(2, ' ') + " - Q" + qual.rjust(2, ' ') + "  -  " + first.ljust(20, ' ') + last.ljust(20, ' ') + "  -  " + str(driverID).rjust(4,' ') + str(race['id']).rjust(4, ' ')
                sys.exit(1)
