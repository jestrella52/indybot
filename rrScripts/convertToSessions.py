#!/usr/bin/env python

import MySQLdb
import MySQLdb.cursors
import datetime
import sys

con = MySQLdb.connect(read_default_group='indybot', port=3306, db='indybot2', cursorclass=MySQLdb.cursors.DictCursor)
cur = con.cursor()

query =  "SELECT race.id, year, title, practice, coverage, green, endcoverage, "
query += "(SELECT COUNT(*) from session where session.race_id = race.id) as sessionCount "
query += "from race JOIN season on race.season_id = season.id "
query += "WHERE year != 2017 AND practice IS Null AND endcoverage IS Null "
query += "ORDER BY green ASC;"

print query

cur.execute(query)
races = cur.fetchall()

for race in races:
    if race['sessionCount'] == 0 and race['year'] == 2015:
        # print str(race['year']) + " " + race['title']
#     if race['green'] != None and race['sessionCount'] == 0:
        query =  "INSERT INTO session (starttime, endtime, race_id, type_id, name) "
        query += "VALUES ('" + str(race['green']) + "', '" + str(race['green']) + "', " + str(race['id']) + ", 1, 'Race');"
        # if race['practice'] == race['coverage'] and race['practice'] == race['green'] and race['practice'] == race['endcoverage']:
            # print str(race['year']) + " " + race['title']
            # query = "UPDATE race SET practice = NULL, endcoverage = NULL WHERE race.id=" + str(race['id']) + ";"
        print query
        cur.execute(query)
        con.commit()
