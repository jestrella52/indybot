import smtplib
import datetime
import urllib
import calendar
import time

from django.db import models
from django.db.models import Count
from django.core import serializers
from django.utils import timezone

from .models import Caution, Course, Race, Result, ResultType, SessionType

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
    thread += winnerList(race_id, output)

    return thread


def link(url, text, output="reddit"):
    if output == "reddit":
        return "[" + text + "](" + url + ")"
    else:
        return "<a href=\"" + url + "\">" + text + "</a>"


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
    courseTable += rs + "Location:" + cs + cs + course.location + " [](/" + course.country.iso + ")" + re + "\n"
    courseTable += rs + "Fast Lap:" + cs + cs + str(course.fastlap) + " mph by " + course.fastdriver.first + " " + course.fastdriver.last + " [](/" + course.fastdriver.country.iso + ") in " + str(course.fastyear) + re + "\n"
    courseTable += rs + "Coordinates:" + cs + cs + link("https://maps.google.com/?q=" + course.gps, course.gps, output) + re + "\n"
    courseTable += rs + "Caution periods:" + cs + cs + "Average of " + str( round(float(totalCautions) / float(len(raceIDs)), 1)  ) + " caution periods per race (over last " + str(len(raceIDs)) + " races)"+ re + "\n"
    courseTable += rs + "Caution lengths:" + cs + cs + "Average of " + str( round(float(totalCautionLaps) / float(totalCautions), 1) ) + " laps per caution period (over last " + str(len(raceIDs)) + " races)" + re + "\n"
    courseTable += "</table>"

    return courseTable
    # query = """SELECT race_id, COUNT(race_id)
    #            FROM caution
    #            WHERE race_id IN
    #             (SELECT id
    #              FROM race
    #              WHERE race.course_id = """ + str(course) + """
    #              AND race.green < CURRENT_DATE)
    #            GROUP BY race_id"""
    #
    # courseData = con.cursor()
    # courseData.execute(query)
    # rows = courseData.fetchall()
    #
    # cautions = 0
    # races = 0
    # for row in rows:
    #     races = races + 1
    #     cautions = cautions + row[1]
    #
    # courseTable += "Average # of Caution Periods:||" + str(round(float(cautions)/float(races), 1)) + " (over last " + str(races) + " races)\n\n"
    #
    # return courseTable

def raceInfo(race_id, output="reddit"):
    race = Race.objects.select_related('course', 'start').get(id=race_id)

    raceTypeValue = SessionType.objects.get(name="Race")

    wolframURL = "http://www.wolframalpha.com/input/?i="

    coverTime = timezone.make_naive(race.coverage)
    greenTime = timezone.make_naive(race.green)

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

    raceTable += bs + link(race.url, race.title, output) + " at the " + race.course.name + be + "\n"
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

    raceTypeValue = ResultType.objects.get(name="Race")

    winners = Result.objects.select_related('race__course', 'driver__country')
    winners = winners.filter(race__course_id=courseValue)
    winners = winners.filter(position=1)
    winners = winners.filter(type_id=raceTypeValue.id)
    winners = winners.order_by('-race.green')


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
        winnerTable += rb + str(winners[i].race.green.year) + cs + winners[i].driver.first + " " + winners[i].driver.last + cs + "[](/" + winners[i].driver.country.iso + ")" + cs + cs
        try:
            winnerTable += str(winners[i+rows].race.green.year) + cs + winners[i+rows].driver.first + " " + winners[i+rows].driver.last + cs + "[](/" + winners[i+rows].driver.country.iso + ")" + cs + cs
        except IndexError, e:
            winnerTable += cs + cs + cs + cs
        try:
            winnerTable += str(winners[i+(rows*2)].race.green.year) + cs + winners[i+(rows*2)].driver.first + " " + winners[i+(rows*2)].driver.last + cs + "[](/" + winners[i+(rows*2)].driver.country.iso + ")" + re
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
