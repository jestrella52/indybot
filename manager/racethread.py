import smtplib
import datetime
import urllib
import calendar
import time

from django.db import models
from django.db.models import Count
from django.core import serializers
from django.utils import timezone

from .models import Caution, Course, Race, Result, ResultType, Session, SessionType

from .support import logit

def sendMail(race, subreddit):
    msg = MIMEText("")
    msg['Subject'] = "Posted in " +subreddit + ": " + race
    msg['From'] = "indybot@valinor.net"
    msg['To'] = "brian@valinor.net"

    s = smtplib.SMTP('localhost')
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()


def compile(race_id, output="reddit"):
    thread = ""

    thread += raceInfo(race_id, output)
    thread += courseInfo(race_id, output)
    thread += grid(race_id, output)
    thread += winnerList(race_id, output)
    thread += footer(output)

    return thread


def link(url, text, output="reddit"):
    if output == "reddit":
        return "[" + text + "](" + url + ")"
    else:
        return "<a href=\"" + url + "\">" + text + "</a>"


def footer(output="reddit"):
    if output == "reddit":
        hr = "***"      # Horizontal Rule
        nl = "\n\n"     # New Line
        ss = "^("       # Small Start
        se = ")"        # Small End
    else:
        hr = "<hr>"
        nl = "<br>"
        ss = ""
        se = ""

    footer  = hr + "\nLive timing and scoring available at " + link("http://racecontrol.indycar.com", "Verizon IndyCar Series Race Control", output) + nl
    footer += link("http://www.indycar.com/Drivers", "Current Driver Standings", output) + nl

    return footer


def gridDriver(driver, output="reddit"):

    fullName = driver.driver.first + " " + driver.driver.last
    twitterURL = "https://twitter.com/" + driver.driver.twitter

    nameplate = link(twitterURL, fullName, output)

    try:
        if (int(driver.driver.rookie) == int(datetime.date.today().year)):
            nameplate += " (R)"
    except Exception, e:
        logit("Error: " + e.args[0])

    nameplate += " " + link("/" + str(driver.driver.country.iso), "", output)

    return nameplate


def grid(race_id, output="reddit"):

    race = Race.objects.get(pk=race_id)
    rowsize = race.rowsize

    entrant = []

    qualTypeValue = ResultType.objects.get(name="Qualification")
    driverList = Result.objects.select_related('driver__country').filter(race__id=race_id).filter(type_id=qualTypeValue).order_by('position')

    # Abandon hope, ye who enter here.
    tableRows = len(driverList) / rowsize
    remainder = len(driverList) % rowsize

    rows = tableRows + (1 if remainder > 0 else 0)

    if output == "reddit":
        bs = "**"
        be = "**"
        nl = "\n\n"
        hr = "***"
        rs = "|"
        re = "|"
        cs = "|"
    else:
        bs = "<strong>"
        be = "</strong>"
        nl = "<br>"
        hr = "<hr>"
        rs = "<tr><td>"
        re = "</td></tr>"
        cs = "</td><td>"

    gridTable  = hr + "\n" + bs + "STARTING GRID" + be + nl

    # TODO: This can be optimized.
    if rowsize == 2:
        if output == "reddit":
            gridTable += "|Position|||Position|\n"
            gridTable += "|:---:|:---:|:---:|:---:|\n"
        else:
            gridTable += "<table>\n"
            gridTable += "<tr><th>Position</th><th></th><th></th><th>Position</th></tr>\n"
    elif rowsize == 3:
        if output == "reddit":
            gridTable += "|Position||||Position|\n"
            gridTable += "|:---:|:---:|:---:|:---:|:---:|\n"
        else:
            gridTable += "<table>\n"
            gridTable += "<tr><th>Position</th><th></th><th></th><th></th><th>Position</th></tr>\n"

    query  = "select driver.first, driver.last, drivercountry.iso, driver.twitter, driver.number, driver.rookie "

    i = 0
    while i < rows:
        if rowsize == 2:
            # Positions & Cars
            gridTable += rs + bs + str(((i+1)*rowsize)-1)
            gridTable += be + cs + link("/car" + str(driverList[((i+1)*rowsize)-2].driver.number), "", output)
            try:
                gridTable += cs + link("/car" + str(driverList[((i+1)*rowsize)-1].driver.number), "", output)
            except IndexError, e:
                gridTable += cs
            gridTable += cs + bs + str((i+1)*rowsize) + be + re + "\n"

            # Nameplate Line
            gridTable += rs + cs + gridDriver(driverList[((i+1)*rowsize)-2], output)
            try:
                gridTable += cs + gridDriver(driverList[((i+1)*rowsize)-1], output)
            except IndexError, e:
                gridTable += cs
            gridTable += cs + re + "\n"

        elif rowsize == 3:
            # Positions & Cars
            gridTable += rs + bs + str(((i+1)*rowsize)-2)
            gridTable += be + cs + link("/car" + str(driverList[((i+1)*rowsize)-3].driver.number), "", output)
            try:
                gridTable += cs + link("/car" + str(driverList[((i+1)*rowsize)-2].driver.number), "", output)
            except IndexError, e:
                gridTable += cs
            try:
                gridTable += cs + link("/car" + str(driverList[((i+1)*rowsize)-1].driver.number), "", output)
            except IndexError, e:
                gridTable += cs
            gridTable += cs + bs + str((i+1)*rowsize) + be + re + "\n"

            # Nameplate Line
            gridTable += rs + cs + gridDriver(driverList[((i+1)*rowsize)-3], output)
            try:
                gridTable += cs + gridDriver(driverList[((i+1)*rowsize)-2], output)
            except IndexError, e:
                gridTable += cs
            try:
                gridTable += cs + gridDriver(driverList[((i+1)*rowsize)-1], output)
            except IndexError, e:
                gridTable += cs
            gridTable += cs + re + "\n"
        i = i + 1

    if output != "reddit":
        gridTable += "</table>"

    return gridTable


def courseInfo(race_id, output="reddit"):
    course_id = Race.objects.get(id=race_id).course_id
    course = Course.objects.select_related('type', 'country', 'fastdriver__country').get(id=course_id)

    cautions = Caution.objects.select_related('race__course').filter(race__course_id=course_id)

    totalCautions = 0
    totalCautionLaps = 0
    raceIDs = set()

    for caution in cautions:
        raceIDs.add(caution.race_id)
        totalCautions = totalCautions + 1
        totalCautionLaps = totalCautionLaps + (caution.endLap - caution.startLap + 1)

    if output == "reddit":
        bs = "**"
        be = "**"
        nl = "\n\n"
        hr = "***"
        rs = ""
        re = ""
        cs = "|"
    else:
        bs = "<strong>"
        be = "</strong>"
        nl = "<br>"
        hr = "<hr>"
        rs = "<tr><td>"
        re = "</td></tr>"
        cs = "</td><td>"

    courseTable  = hr + nl + bs + "CIRCUIT INFORMATION: " + link(course.url, course.name, output) + be + nl

    if output == "reddit":
        courseTable += "||||\n:--|:--|:--\n"
    else:
        courseTable += "<table>"

    courseTable += rs + "Length:" + cs + cs + str(course.length) + " miles" + re + "\n"
    courseTable += rs + "Type:" + cs + cs + course.type.type + re + "\n"
    courseTable += rs + "Location:" + cs + cs + course.location + " " + link("/" + course.country.iso, "", output) + re + "\n"
    courseTable += rs + "Fast Lap:" + cs + cs + str(course.fastlap) + " mph by " + course.fastdriver.first + " " + course.fastdriver.last + " " + link("/" + course.fastdriver.country.iso, "", output) + " in " + str(course.fastyear) + re + "\n"
    courseTable += rs + "Coordinates:" + cs + cs + link("https://maps.google.com/?q=" + course.gps, course.gps, output) + re + "\n"

    try:
        courseTable += rs + "Caution periods:" + cs + cs + "Average of " + str( round(float(totalCautions) / float(len(raceIDs)), 1)  ) + " caution periods per race (over last " + str(len(raceIDs)) + " races)"+ re + "\n"
        courseTable += rs + "Caution lengths:" + cs + cs + "Average of " + str( round(float(totalCautionLaps) / float(totalCautions), 1) ) + " laps per caution period (over last " + str(len(raceIDs)) + " races)" + re + "\n"
    except ZeroDivisionError:
        pass

    if output != "reddit":
        courseTable += "</table>"

    return courseTable


def raceInfo(race_id, output="reddit"):
    race = Race.objects.select_related('course', 'start').get(id=race_id)

    sessionTypeValue = SessionType.objects.get(name="Race")
    raceSession = Session.objects.filter(type_id=sessionTypeValue.id).filter(race_id=race_id)[0]

    wolframURL = "http://www.wolframalpha.com/input/?i="

    coverTime = timezone.make_naive(raceSession.tvstarttime)
    greenTime = timezone.make_naive(raceSession.starttime)

    coverageURL = wolframURL + urllib.quote(str(coverTime) + " " + coverTime.strftime("%p") + " EDT in UTC")
    greenURL = wolframURL + urllib.quote(str(greenTime) + " " + greenTime.strftime("%p") + " EDT in UTC")

    raceTable  = "Welcome to the /r/INDYCAR race thread for the "

    if output == "reddit":
        bs = "**"
        be = "**"
        nl = "\n"
        hr = "***"
        rs = ""
        re = ""
        cs = "|"
    else:
        bs = "<strong>"
        be = "</strong>"
        nl = "<br>"
        hr = "<hr>"
        rs = "<tr><td>"
        re = "</td></tr>"
        cs = "</td><td>"

    raceTable += bs + link(race.url, race.title, output) + " at " + race.course.name + be + "\n"
    raceTable += hr + nl + nl
    raceTable += bs + "WHEN/WHERE TO WATCH" + bs

    if output == "reddit":
        raceTable += "\n\n||||\n:--|:--|:--\n"
    else:
        raceTable += "<table>"

    raceTable += rs + "Televised By:" + cs + cs + race.channel + re + "\n"
    raceTable += rs + "Coverage Starts:" + cs + cs + link(coverageURL, coverTime.strftime("%A, %l:%M%p EDT on %b %d, %Y"), output) + re + "\n"
    raceTable += rs + "Green Flag Flies:" + cs + cs + link(greenURL, greenTime.strftime("%A, %l:%M%p EDT on %b %d, %Y"), output) + re + "\n"
    raceTable += rs + "Start:" + cs + cs + race.start.type + re + "\n\n"

    if output != "reddit":
        raceTable += "</table>"

    return raceTable


def winnerList(race_id, output="reddit"):

    race = Race.objects.get(id=race_id)
    courseValue = race.course_id

    resultTypeValue = ResultType.objects.get(name="Race")
    sessionTypeValue = SessionType.objects.get(name="Race")

    raceSessions = Session.objects.filter(race__course_id=courseValue).filter(type_id=sessionTypeValue.id).order_by('-starttime')

    winners = []
    for raceSession in raceSessions:
        try:
            race = Race.objects.get(id=raceSession.race_id)
            winners.append(Result.objects.get(race_id=raceSession.race_id, type_id=resultTypeValue.id, position=1))
        except:
            pass


    if output == "reddit":
        header = "|Year|Winner|Country|"
        spacer = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        winnerTable  = "***\n\n**PREVIOUS WINNERS**\n\n"
        winnerTable += header + spacer + header + spacer + header + "\n"
        winnerTable += ":--:|:--|:--:|:--:|:--:|:--|:--:|:--:|:--:|:--|:--:\n"
    else:
        winnerTable  = "<hr><br><strong>PREVIOUS WINNERS</strong><br><br>"
        winnerTable += "<table><tr>"
        winnerTable += "<th>Year</th><th>Winner</th><th>Country</th>" + "<th></th>"
        winnerTable += "<th>Year</th><th>Winner</th><th>Country</th>" + "<th></th>"
        winnerTable += "<th>Year</th><th>Winner</th><th>Country</th>" + "</tr>"

    if output == "reddit":
        rb = ""             # Row Beginning
        re = ""             # Row End
        cs = "|"            # Cell Separator
    else:
        rb = "<tr><td>"   # Row Beginning
        re = "</td></tr>" # Row End
        cs = "</td><td>"  # Cell Separator

    tableRows = len(winners) / 3
    remainder = len(winners) % 3
    rows = tableRows + (1 if remainder > 0 else 0)

    # Abandon hope, ye who enter here.
    i = 0
    while i < rows:
        # winnerTable += rb + str(winners[i].race.green.year) + cs + winners[i].driver.first + " " + winners[i].driver.last + cs + link("/" + winners[i].driver.country.iso, "", output) + cs + cs
        winnerTable += rb + str(winners[i].race.season.year) + cs + winners[i].driver.first + " " + winners[i].driver.last + cs + link("/" + winners[i].driver.country.iso, "", output) + cs + cs
        try:
            winnerTable += str(winners[i+rows].race.season.year) + cs + winners[i+rows].driver.first + " " + winners[i+rows].driver.last + cs + link("/" + winners[i+rows].driver.country.iso, "", output) + cs + cs
        except IndexError, e:
            winnerTable += cs + cs + cs + cs
        try:
            winnerTable += str(winners[i+(rows*2)].race.season.year) + cs + winners[i+(rows*2)].driver.first + " " + winners[i+(rows*2)].driver.last + cs + link("/" + winners[i+(rows*2)].driver.country.iso, "", output) + re
        except IndexError, e:
            winnerTable += cs + cs + re
        winnerTable += "\n"
        i = i + 1

    if output != "reddit":
        winnerTable += "</table>\n"

    if len(winners) > 0:
        return winnerTable
    else:
        return ""
