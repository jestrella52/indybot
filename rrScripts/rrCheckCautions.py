#!/usr/bin/env python

#
#   Adds caution reasons to database.
#

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

con = MySQLdb.connect(read_default_group='indybot', port=3306, db='indybot2', cursorclass=MySQLdb.cursors.DictCursor)
cur = con.cursor()

query = "SELECT * from driver"
cur.execute(query)
drivers = cur.fetchall()

query = "SELECT * from caution_reason"
cur.execute(query)
cautionReasons = cur.fetchall()

ddb = []
inserted = []

resultPattern = re.compile('^<TR .*><TD .*>(\d+)</TD><TD .*>\s?(\d+)</TD><TD .*><A HREF=.*>\s?(\d+)</A></TD><TD class=col><IMG .*> &nbsp; <A HREF=/driver/[a-zA-Z\.\-\,_]+>([a-zA-Z\.\-]+) ([a-zA-Z\.\-\'\s]+)</A>')
flagPattern = re.compile('^<TR .*><TD .*><IMG SRC=/images/(\w+)_flag.png.*></TD><TD .*>(\d+)</TD><TD .*>(\d+)</TD><TD .*>(\d+)</TD><TD class=col>(.*)</TD><TD class=col>&nbsp;</TD></TR>')

f = open('cautions.txt', 'r')
for line in f:
    match = flagPattern.match(line)
    if match:
        numbers = ""
        what    = ""
        where   = ""

        if match.group(1) != "green":
            startLap    = match.group(2)
            endLap      = match.group(3)
            reason      = match.group(5).replace('&nbsp;', '').strip().split()

            if reason[0][0] == "#":
                numbers     = reason.pop(0).replace('#', '').split(',')
                if len(reason) == 0:
                    what = "Accident"
                elif reason[0].lower() == "accident/fire":
                    what = "Accident"
                elif reason[0].lower() == "off" and reason[1].lower() == "course":
                    what = "Off Course"
                    del reason[0:2]
                    where = " ".join(reason).title()
                elif reason[0].lower() == "lost" and reason[1].lower() == "power":
                    what = "Stopped"
                    del reason[0:2]
                    where = " ".join(reason).title()
                elif reason[0].lower() == "lost" and (reason[1].lower() == "tire" or reason[1].lower() == "wheel"):
                    what = "Lost Wheel"
                    del reason[0:2]
                    where = " ".join(reason).title()
                elif reason[0].lower() == "turn":
                    what = "Accident"
                    where = " ".join(reason).title()
                elif reason[0].lower() == "suspension" or reason[0].lower() == "tire":
                    what = "Mechanical"
                elif reason[0].lower() == "lost":
                    what = " ".join(reason).title()
                elif reason[0].lower() == "out" and reason[1].lower() == "of" and reason[2].lower() == "fuel":
                    what = "Out Of Fuel"
                elif reason[0].lower() == "oil" and reason[1].lower() == "on" and reason[2].lower() == "track":
                    what = "Leak"
                elif reason[0].lower() == "oiling":
                    what = "Leak"
                elif len(reason) > 1 and reason[0].lower() == "brushed" and reason[1].lower() == "wall":
                    what = "Accident"
                    del reason[0:2]
                    where = " ".join(reason).title()
                elif len(reason) > 1 and reason[0].lower() == "light" and reason[1].lower() == "contact":
                    what = "Accident"
                    del reason[0:2]
                    where = " ".join(reason).title()
                elif len(reason) > 1 and reason[0].lower() == "engine" and reason[1].lower() == "spray":
                    what = "Leak"
                elif len(reason) > 1 and reason[0].lower() == "water" and reason[1].lower() == "leak":
                    what = "Leak"
                elif len(reason) > 1 and reason[0].lower() == "engine" and reason[1].lower() == "fire":
                    what = "Engine"
                elif reason[0].lower() == "spray":
                    what = "Leak"
                elif reason[0].lower() == "smoking":
                    what = "Smoke"
                else:
                    what  = reason.pop(0).title()
                    where = " ".join(reason).title()

                # for victim in numbers:
                #     idx = next(index for (index, d) in enumerate(ddb) if d["number"] == victim)
                #     print ddb[idx]['last'] + ", " + ddb[idx]['first']
            elif reason[0].lower() == "cold/wind":
                what = "Track Temperature"
            elif reason[0] == "restart" and reason[1] == "from" and reason[2] == "red" and reason[3] == "flag":
                what = "Red Flag Restart"
                del reason[0:4]
            elif len(reason) >= 4 and (reason[0] == "red" and reason[1] == "flag" and (reason[2] == "restart" or reason[3] == "restart")):
                what = "Red Flag Restart"
                del reason[0:3]
            elif len(reason) >= 3 and reason[0] == "red" and reason[1] == "flag" and reason[2] == "restart":
                what = "Red Flag Restart"
                del reason[0:3]
            elif reason[0] == "red" and reason[1] == "flag":
                what = "Red Flag Restart"
                del reason[0:2]
            elif (reason[0] == "no" or reason[0] == "aborted") and reason[1] == "start":
                what = "Aborted Start"
                del reason[0:2]
            elif reason[0] == "rain/hail" or reason[0] == "rain":
                what = "Precipitation"
            elif reason[0] == "rain;" and reason[1] == "yellow" and reason[2] == "restart":
                what = "Precipitation"
                del reason[0:3]
            elif reason[0] == "oil" and reason[1] == "on" and reason[2] == "track":
                what = "Leak"
                del reason[0:3]
            elif reason[0] == "light" and reason[1] == "contact":
                what = "Accident"
                del reason[0:2]
                where = " ".join(reason).title()
            elif reason[0] == "track" and reason[1] == "inspection":
                what = "Track Inspection"
                del reason[0:2]
            elif reason[0] == "track" and reason[1] == "lights":
                what = "Track Lights"
                del reason[0:2]
                where = " ".join(reason).title()
            elif reason[0] == "engine" and reason[1] == "spray":
                what = "Leak"
                del reason[0:2]
                where = " ".join(reason).title()
            elif reason[0] == "grass" and reason[1] == "fire":
                what = "Grass Fire"
                del reason[0:2]
                where = " ".join(reason).title()
            elif reason[0] == "smoking":
                what = "Smoke"
            elif reason[0] in ["rain", "debris", "moisture", "accident", "rain/hail", "cold/wind", "wildlife"]:
                what = reason[0].title()
                where = " ".join(reason[1:]).title()

            if where.lower() == "in pits" or where.lower() == "pits":
                where = "Pit Lane"
            elif where.lower() == "pit entry":
                where = "Pit In"
            elif where.lower() == "pit exit":
                where = "Pit Out"

            # if what == "Accident":
            #     continue
            # elif what == "Debris" or what == "Track Inspection" or what == "Spun" or what == "Tow-In" or what == "Stalled":
            #     continue
            # elif what == "Rain" or what == "Moisture" or what == "Aborted Start" or what == "Grass Fire":
            #     continue
            # elif what == "Oil On Track" or what == "Smoke" or what == "Red Flag Restart" or what == "Engine":
            #     continue
            # elif what == "Fire" or what == "Slow" or what == "Wildlife" or what == "Off Course" or what == "Leak":
            #     continue
            # elif what == "Stopped" or what.split()[0] == "Lost" or what == "Track Lights":
            #     continue

            if what not in inserted:
                query = "INSERT INTO caution_reason (reason) VALUES ('" + what + "')"
                cur.execute(query)
                con.commit()
                inserted.append(what)
            # print query
            # print " ".join(numbers).ljust(32, ' ') + startLap.rjust(5, ' ') + endLap.rjust(5, ' ') + "  " + what.ljust(20, ' ') + "  " + where.ljust(20, ' ')

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
