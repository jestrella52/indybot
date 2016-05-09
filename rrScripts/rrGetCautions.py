#!/usr/bin/env python

import MySQLdb
import MySQLdb.cursors
import pycurl
import getopt
import re

class Page:
    def __init__(self):
        self.contents = ''

    def body_callback(self, buf):
        self.contents = self.contents + buf

user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36")

con = MySQLdb.connect(read_default_group='indybot', port=3306, db='indybot2', cursorclass=MySQLdb.cursors.DictCursor)
cur = con.cursor()

query = "SELECT * from race where urlrr != \"\" AND urlrr IS NOT NULL"
cur.execute(query)
races = cur.fetchall()

flagPattern = re.compile('^<TR .*><TD .*><IMG SRC=/images/(\w+)_flag.png.*></TD><TD .*>(\d+)</TD><TD .*>(\d+)</TD><TD .*>(\d+)</TD><TD class=col>(.*)</TD><TD class=col>&nbsp;</TD></TR>')

f = open('cautions.txt', 'w')

for race in races:

    print "--- Processing: " + race['title']
    url = race['urlrr']
    c = pycurl.Curl()
    page = Page()
    c.setopt(pycurl.URL, url)
    c.setopt(c.WRITEFUNCTION, page.body_callback)
    c.perform()
    c.close()
    lines = page.contents.split('\n')

    for line in lines:
        match = flagPattern.match(line)
        if match:
            f.write(line + "\n")

f.close()
