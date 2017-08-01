#!/usr/bin/env python

import os
import sys
import time
import pytz
import praw
import django
import datetime

# from celery import Celery
# from celery.schedules import crontab
# from celery.backends.rpc import RPCBackend
from slackclient import SlackClient

from manager.tasks import UploadLiveriesTask

from manager.models import Post, Race, Session

BOT_ID = "U1B41SSLR"
BOT_TOKEN = "xoxb-45137910705-xkRY9dxy9j79Pf7izR3LkzHa"

AT_BOT = "<@" + BOT_ID + ">"

slack_client = SlackClient(BOT_TOKEN)

user_agent	= ("/r/IndyCar crew chief v1.9.1 by /u/Badgerballs")


def redditLockThread(subid):
    r = praw.Reddit(user_agent=user_agent)
    r.refresh_access_information()
    postToLock = r.get_submission(submission_id=targetRedditThreadID)
    postToLock.lock()


def usageLock():
    response = "lock <threadtype>: Lock a Reddit thread\n"
    response = response + "----------\n"
    response = response + "Valid thread types are:\n"
    response = response + "practice  race  postrace\n"
    return response


def lockThread(command):
    eventID = getCurrentEvent()
    try:
        targetThread = command.split()[1]
    except IndexError:
        return usageLock()

    response = "You want me to lock the " + targetThread + " thread.\n"

    if targetThread == "race":
        threadTypeID = 1
    elif targetThread == "postrace":
        threadTypeID = 5
    elif targetThread == "practice":
        threadTypeID = 3
    else:
        return "Sorry.  Valid threads are 'practice', 'race', and 'postrace'."

    targetSession = Session.objects.filter(race__id=eventID, type_id=threadTypeID, submission_id__isnull=False)
    if targetSession.count() == 1:
        post = Post.objects.get(id=targetSession[0].submission_id)
        response = response + "Found " + str(targetSession[0].name)
        response = response + " with reddit submission id: " + str(post.submission) + "\n"
        # targetRedditThreadID = "6f92or"
        # redditLockThread(post.submission)
        response = response + "I think I locked it."
    elif targetSession.count() > 1:
        response = response + "I found multiple " + targetThread + " threads.  I'm not smart enough to handle this yet."
    else:
        response = response + "No " + targetThread + " threads found."

    return response


def checkered():
    response = "Oops."
    raceID = getCurrentEvent()
    postRaceStart = datetime.datetime.now(pytz.timezone('US/Eastern'))
    postRaceEnd = postRaceStart + datetime.timedelta(minutes=10)

    postRaceSession = Session.objects.filter(race__id=raceID, type_id=5, submission_id__isnull=True)
    if postRaceSession.count() == 1:
        session = Session.objects.get(id=postRaceSession[0].id)
        session.posttime = postRaceStart
        session.starttime = postRaceStart
        session.endtime = postRaceEnd
        session.save()
        response = "Starter copies.  Checkered flag!  Post-race thread is rolling."

    return response


def findThreads(raceID):
    eventSessions = Session.objects.filter(race_id=412).exclude(posttime__isnull=True)
    response = "Found " + str(eventSessions.count()) + " sessions with posts scheduled.\n"
    for session in eventSessions:
        if session.submission_id:
            redditID = Post.objects.get(id=session.submission_id).submission
            response = response + session.name + " - " + str(session.posttime) + " - " + redditID + "\n"
        else:
            response = response + session.name + " - " + str(session.posttime) + "\n"
    return response


def getCurrentEvent():
    todayStart = datetime.datetime.now(pytz.timezone('US/Eastern')).replace(day=25, hour=0, minute=0, second=0)
    todayEnd = datetime.datetime.now(pytz.timezone('US/Eastern')).replace(day=25, hour=23, minute=59, second=59)
    response = "Ooops"

    todaySessions = Session.objects.filter(
        type_id=1
    ).exclude(
        endtime__lte=todayStart
    ).exclude(
        starttime__gte=todayEnd
    )
    if todaySessions.count() == 1:
        return todaySessions[0].race_id
    else:
        return False


def findEvent():
    todayStart = datetime.datetime.now(pytz.timezone('US/Eastern')).replace(day=25, hour=0, minute=0, second=0)
    todayEnd = datetime.datetime.now(pytz.timezone('US/Eastern')).replace(day=25, hour=23, minute=59, second=59)
    response = "Ooops"

    todaySessions = Session.objects.filter(
        type_id=1
    ).exclude(
        endtime__lte=todayStart
    ).exclude(
        starttime__gte=todayEnd
    )
    if todaySessions.count() == 1:
        raceID = todaySessions[0].race_id
        todayRace = Race.objects.get(id=todaySessions[0].race_id)
        response = "Today's race is the " + todayRace.title + "."
        response = response + findThreads(raceID)
    elif todaySessions.count() > 1:
        response = "I found multiple races.  This confuses and scares me."
    else:
        response = "I don't know of any races happening today."
    return response


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean."
    if command.startswith("checkered"):
        response = checkered()
    elif command.startswith("event"):
        response = findEvent()
    elif command.startswith("lock"):
        response = lockThread(command)
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    pid = str(os.getpid())
    pidfile = "/tmp/indybot.pid"

    if os.path.isfile(pidfile):
        print "%s already exists, exiting." % pidfile
        sys.exit()
    file(pidfile, 'w').write(pid)

    try:
        READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
        if slack_client.rtm_connect():
            print("IndyBot connected and running!")
            while True:
                command, channel = parse_slack_output(slack_client.rtm_read())
                if command and channel:
                    handle_command(command, channel)
                time.sleep(READ_WEBSOCKET_DELAY)
        else:
            print("Connection failed. Invalid Slack token or bot ID?")

    finally:
        os.unlink(pidfile)
