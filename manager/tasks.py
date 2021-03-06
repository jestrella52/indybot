import datetime
import dateutil
import requests
import twitter
import pycurl
import shutil
import django
import arrow
import praw
import time
import re
import os

from PIL import Image
from lxml import html
from time import sleep
from celery import Celery
from celery.schedules import crontab
from celery.backends.rpc import RPCBackend
from datetime import date, timedelta
from ics import Calendar, Event

os.environ['DJANGO_SETTINGS_MODULE'] = 'indybot.settings'
django.setup()

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django_slack import slack_message

from jobtastic import JobtasticTask

from .models import Country, Driver, Post, Race, RedditAccount, Season, Session
from .models import SessionType, Tweet

from .racethread import compile

from .support import logit

app = Celery('indybot-' + settings.INDYBOT_ENV, backend='amqp', broker='amqp://guest@localhost//')
rpc_backend = RPCBackend(app)

if settings.INDYBOT_ENV == "PROD":
    logit("Applying PROD schedule.")
    app.conf.update(
        CELERYBEAT_SCHEDULE = {
            'check-threads': {
                'task': 'manager.tasks.RedditThreadTask',
                'schedule': crontab(hour='*', minute='*'),
                'kwargs': {'stamp': str(time.time())},
            },
            'update-sidebar': {
                'task': 'manager.tasks.UpdateRedditSidebarTask',
                'schedule': datetime.timedelta(minutes=5),
                'kwargs': {'stamp': str(time.time())},
            },
            'check-posts': {
                'task': 'manager.tasks.RedditPostsTask',
                'schedule': datetime.timedelta(minutes=1),
                'kwargs': {'stamp': str(time.time())},
            },
            'generate-liveries': {
                'task': 'manager.tasks.GenerateLiveriesTask',
                'schedule': crontab(hour='4', minute='0'),
                'kwargs': {'stamp': str(time.time())},
            },
            'upload-liveries': {
                'task': 'manager.tasks.UploadLiveriesTask',
                'schedule': crontab(hour='4', minute='30'),
                'kwargs': {'stamp': str(time.time())},
            },
            'check-tweets': {
                'task': 'manager.tasks.TweetTask',
                'schedule': datetime.timedelta(seconds=30),
                'kwargs': {'stamp': str(time.time())},
            },
        }
    )
elif settings.INDYBOT_ENV == "STAGE":
    logit("Applying STAGE schedule.")
    app.conf.update(
        CELERYBEAT_SCHEDULE = {
            #'check-threads': {
            #    'task': 'manager.tasks.RedditThreadTask',
            #    'schedule': crontab(hour='*', minute='*'),
            #    'kwargs': {'stamp': str(time.time())},
            #},
            #'check-posts': {
            #    'task': 'manager.tasks.RedditPostsTask',
            #    'schedule': datetime.timedelta(minutes=1),
            #    'kwargs': {'stamp': str(time.time())},
            #},
            'generate-calendar': {
                'task': 'manager.tasks.GenerateCalendarTask',
                'schedule': datetime.timedelta(minutes=1),
                'kwargs': {'stamp': str(time.time())},
            },
        }
    )
elif settings.INDYBOT_ENV == "DEVEL":
    logit("Applying DEVEL schedule.")
    app.conf.update(
        CELERYBEAT_SCHEDULE = {
            'check-threads': {
                'task': 'manager.tasks.RedditThreadTask',
                'schedule': crontab(hour='*', minute='*'),
                'kwargs': {'stamp': str(time.time())},
            },
            'check-posts': {
                'task': 'manager.tasks.RedditPostsTask',
                'schedule': datetime.timedelta(minutes=1),
                'kwargs': {'stamp': str(time.time())},
            },
        }
    )

posterCredits  = "***\n\nIndyBot submitted this post on behalf of /u/"
indybotCredits = "***\n\n^(Questions, comments, or hate mail regarding IndyBot should be directed to /u/BadgerBalls.)\n"


# def logit(message):
#     with open(settings.INDYBOT_LOGFILE, "a") as myfile:
#         myfile.write(message + "\n")


# def bumpLog():
#     with open(settings.INDYBOT_LOGFILE, "a") as myfile:
#         myfile.write("\n\n")


class TweetTask(JobtasticTask):
    backend = rpc_backend
    herd_avoidance_timeout = 20
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):
        tweets = Tweet.objects.filter(tid=None).filter(Q(publish_time__lte=timezone.now()))

        if len(tweets) > 0:
            logit(str(len(tweets)) + " tweets in queue")
            api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                              consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                              access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
                              access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET)
            #TODO : Verify that we've successfully logged in.
            try:
                api.VerifyCredentials()

                for tweet in tweets:
                    status = api.PostUpdate(tweet.text)
                    logit("STATUS: " + str(status))
                    tweet.tid = status.id
                    tweet.save()
            except twitter.TwitterError as e:
                logit("TWITTER ERROR: Code: " + str(e))

        self.update_progress(100, 100)
        return 1


class GenerateCalendarTask(JobtasticTask):
    backend = rpc_backend
    herd_avoidance_timeout = 55
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):
        logit("[Calendar] GenerateCalendarTask: starting up! - - - - - - - - - -")
        sessionTypeValue = SessionType.objects.get(name="Race")
        currentSeason = Season.objects.filter(year=date.today().year)
        # logit("[Calendar] Current Season: " + str(currentSeason[0].year))

        localtz = dateutil.tz.tzlocal()
        localoffset = localtz.utcoffset(datetime.datetime.now(localtz))
        offsetHours = localoffset.total_seconds() / 3600

        # logit("[Calendar] Offset: " + str(offsetHours))

        calendar = Calendar()
        calendar.creator = unicode("IndyBot, a product of /r/INDYCAR on Reddit")

        raceList = Race.objects.filter(season=currentSeason)
        for i in xrange(len(raceList)):
            # logit("[Calendar] ----------------------------------------------- ")
            # logit("[Calendar] " + raceList[i].title)
            event = Event()
            event.name = raceList[i].title
            event.location = raceList[i].course.name
            event.description = "Coverage on " + raceList[i].channel

            startTime = False
            endTime = False
            raceSession = Session.objects.get(race_id=raceList[i].id, type_id=sessionTypeValue)
            startTime = raceSession.tvstarttime + timedelta(hours=offsetHours)

            if raceSession.tvendtime == None:
                endTime = startTime + timedelta(hours=3)
            else:
                endTime = raceSession.tvendtime + timedelta(hours=offsetHours)

            event.begin = arrow.get(startTime, 'US/Eastern')
            event.end = arrow.get(endTime, 'US/Eastern')

            # logit("[Calendar] Start Time: " + str(event.begin.format('YYYY-MM-DD HH:mm:ss ZZ')))
            # logit("[Calendar] End Time: " + str(event.end.format('YYYY-MM-DD HH:mm:ss ZZ')))

            calendar.events.append(event)


        with open('static/races.ics', 'w') as f:
            f.writelines(calendar)

        logit("[Calendar] Finished.")

        return 1


class RedditThreadTask(JobtasticTask):
    backend = rpc_backend
    herd_avoidance_timeout = 55
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):
        logit("[Threads] RedditThreadTask: starting up! - - - - - - - - - - - - ")
        user_agent	= ("/r/IndyCar crew chief v1.9.1 by /u/Badgerballs")

        pracSessionID = SessionType.objects.filter(name="Practice").values('id')[0]['id']
        qualSessionID = SessionType.objects.filter(name="Qualification").values('id')[0]['id']
        raceSessionID = SessionType.objects.filter(name="Race").values('id')[0]['id']
        contSessionID = SessionType.objects.filter(name="Race (Resumed)").values('id')[0]['id']
        postSessionID = SessionType.objects.filter(name="Post-Race").values('id')[0]['id']

        # logit("[Threads] Practice: " + str(pracSessionID))
        # logit("[Threads] Qualification: " + str(qualSessionID))
        # logit("[Threads] Race: " + str(raceSessionID))
        # logit("[Threads] Race resumed: " + str(contSessionID))
        # logit("[Threads] Post-race: " + str(postSessionID))

        now = timezone.now()

        # Get posts whose post times have passed but have no submission id
        upcomingSessions = Session.objects.filter(submission_id__isnull=True)
        upcomingSessions = upcomingSessions.filter(posttime__isnull=False)
        upcomingSessions = upcomingSessions.filter(posttime__lte=now)
        upcomingSessions = upcomingSessions.order_by('posttime')

        # logit("[Threads] Upcoming Sessions: " + str(upcomingSessions.query))

        # Only post if the session hasn't already ended
        for sess in upcomingSessions:

            # Set our defaults
            postAuthor = 1
            postCredit = 0

            if sess.posttime:
                postPubTime = sess.posttime
                postModTime = sess.posttime
            else:
                postPubTime = sess.starttime
                postModTime = sess.starttime

            postFlairCSS = 'race'
            postSticky = 1
            postStream = 1
            postSort = 'new'

            if sess.endtime >= now:

                eventName = str(datetime.datetime.now().year) + " " + sess.race.title

                if sess.type.id == pracSessionID or sess.type.id == qualSessionID:
                    logit("[Threads] Posting practice/qual thread.")
                    postTitle = "[Practice/Qual Thread] - " + eventName
                    postBody = "This thread is for discussion of all things related to practice and qualifying for the " + sess.race.title + "\n"
                    postFlairText='Practice Thread'


                elif sess.type.id == raceSessionID or sess.type.id == contSessionID:
                    logit("[Threads] Posting race thread.")
                    postTitle = "[Race Thread] - " + eventName
                    postBody = compile(sess.race.id)
                    logit("[Threads] Compiled Race Thread")
                    postFlairText='Race Thread'

                elif sess.type.id == postSessionID:
                    logit("[Threads] Posting post-race thread.")
                    postTitle = "[Post-Race Thread] - " + eventName
                    postBody = "This thread is for discussion of the results and post-race happenings of the " + sess.race.title + "\n"
                    postFlairText='Post-Race Thread'
                    postStream = 0

                else:
                    logit("[Threads] Fuck it.  No idea what to post.")

                # We have a post to post.  Let's post our post.
                if postTitle and postBody:
                    logit("[Threads] " + postTitle)
                    postObj = Post(
                        title=postTitle,
                        body=postBody,
                        author_id=postAuthor,
                        publish_time=postPubTime,
                        modified_time=postModTime,
                        flair_text=postFlairText,
                        flair_css_class=postFlairCSS,
                        sort=postSort,
                        sticky=postSticky,
                        stream=postStream,
                        credit=postCredit
                    )
                    postObj.save()
                    logit("[Threads] Post Object Saved.  ID: " + str(postObj.id))
                    sess.submission_id = postObj.id
                    sess.save()
                    logit("[Threads] Session updated with post id.")

                    # Publish instantly.
                    ts = str(time.time())
                    result = RedditPostsTask.delay_or_fail(stamp=ts)
                    logit("[Threads] Submitted RPT Task.")

        logit("[Threads] Finished.")
        return True


class RedditPostsTask(JobtasticTask):
    backend = rpc_backend
    herd_avoidance_timeout = 20
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):
        logit("[Posts] RedditPostsTask: starting up! - - - - - - - - - - - -")
        user_agent	= ("/r/IndyCar crew chief v1.9.1 by /u/Badgerballs")

        posts = Post.objects.filter(submission=None).filter(Q(publish_time__lte=timezone.now())).prefetch_related('author')
        logit("[Posts] " + str(len(posts)) + " posts in queue.")

        if len(posts) > 0:
            r = praw.Reddit(client_id=settings.REDDIT_CLIENT_ID,
                            client_secret=settings.REDDIT_CLIENT_SECRET,
                            username=settings.REDDIT_USERNAME,
                            password=settings.REDDIT_PASSWORD,
                            user_agent=user_agent)

            if r.user == None:
                logit("[Posts] Failed to log in. Something went wrong!")
            else:
                logit("[Posts] Logged in to reddit as " + str(r.user))
                sub = r.subreddit(settings.SUBREDDIT)

            for post in posts:
                postBody = post.body

                if post.credit:
                    postBody = postBody + "\n\n" + posterCredits + str(post.author) + "\n"

                postBody += indybotCredits

                submission = sub.submit(post.title, selftext=postBody)

                if post.flair_text and post.flair_css_class:
                    #TODO Find where these are set and update this to better work with new PRAW
                    availableFlair = submission.flair.choices()
                    for flairChoice in availableFlair:
                        if flairChoice['flair_css_class'] == "race":
                            submission.flair.select(flairChoice['flair_template_id'], post.flair_text)

                if post.sort:
                    submission.mod.suggested_sort(sort=post.sort)

                if post.sticky:
                    submission.mod.sticky()

                if post.stream:
                    comment = submission.reply("Please post stream links as a reply to this stickied comment.")
                    comment.mod.distinguish(how='yes', sticky=True)

                post.submission = submission.id
                post.save()

                logit("[Posts] " + post.title + ", by " + str(post.author))
                logit("[Posts] Scheduled for: " + str(post.publish_time))
                timePub = timezone.make_naive(post.publish_time)
                timeNow = timezone.make_naive(timezone.now())
                logit("[Posts] Adjusted time: " + str(timePub))
                logit("[Posts] Current time: " + str(timeNow))
                if (timeNow >= timePub):
                    logit ("[Posts] POSTING!")

        self.update_progress(100, 100)

        return 1


class UpdateRedditSidebarTask(JobtasticTask):
    backend = rpc_backend
    herd_avoidance_timeout = 60
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):

        logit("[Sidebar] RedditSidebarTask: starting up! - - - - - - - - - - - -")
        user_agent	= ("/r/IndyCar crew chief v1.9.1 by /u/Badgerballs")

        message = ""
        percentage = float(0)

        r = praw.Reddit(client_id=settings.REDDIT_CLIENT_ID,
                        client_secret=settings.REDDIT_CLIENT_SECRET,
                        username=settings.REDDIT_USERNAME,
                        password=settings.REDDIT_PASSWORD,
                        user_agent=user_agent)

        if r.user == None:
            loginMessage = "Failed to log in to reddit. Something went wrong!"
        else:
            loginMessage = "Logged in to reddit as " + str(r.user)

        logit("[Sidebar] " + loginMessage)
        message += loginMessage + "\n"
        self.update_progress(20, 100)

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        #
        # BELOW CODE TAKEN FROM OLD INDYBOT SCRIPT.  USED FOR UPDATING 500 COUNTDOWN.
        # NOT TESTED IN DJANGO VERSION, JUST HERE FOR MODIFICATION/REUSE NEXT YEAR.
        #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # query  = "SELECT race.coverage FROM race WHERE course_id = 1 AND "
        # query += "green >= '" + datetime.datetime.now().strftime("%Y-%m-%d")
        # query += " 00:00:00' ORDER BY coverage ASC LIMIT 1"
        #
        # indyCur = con.cursor()
        # indyCur.execute(query)
        # daysToIndy = (indyCur.fetchone()[0].date() - datetime.date.today()).days
        #
        # ## Update Indy 500 countdown
        # if daysToIndy > 0:
        #     countdownText = "### [" + str(daysToIndy) + " Days until the Indy 500!]"
        # elif daysToIndy == 0:
        #     countdownText = "### [Drivers, START YOUR ENGINES!]"
        #
        # sidebar = re.sub("### \[Drivers, START YOUR ENGINES!\]", countdownText, sidebar, flags=re.S)
        # sidebar = re.sub("### \[\d+ Days until the Indy 500!\]", countdownText, sidebar, flags=re.S)

        # logit("[Sidebar] Getting subreddit")
        sub = r.subreddit(settings.SUBREDDIT)
        mod = sub.mod
        subSettings = mod.settings()
        oldSidebar = subSettings['description']

        sidebar = oldSidebar

        start = timezone.make_aware(datetime.datetime(datetime.date.today().year, 1, 1))
        end = timezone.make_aware(datetime.datetime(datetime.date.today().year, 12, 31))
        sessions = Session.objects.filter(type_id=1).filter(starttime__gte=start).filter(starttime__lte=end).order_by('starttime').select_related()

        # logit("[Sidebar] Found " + str(len(sessions)) + " sessions.")
        foundNext = 0
        highlightRow = 0
        raceCount = 0

        schedTable  = "### 2018 IndyCar Schedule\n\n"
        schedTable += "**Date**|**Course**|**Time**|**TV**\n"
        schedTable += ":---|:---|:---|:---\n"

        for session in sessions:

            raceCount = raceCount + 1
            coverageStart = timezone.make_naive(session.starttime)
            coverageEnd = timezone.make_naive(session.endtime)
            timeNow = timezone.make_naive(timezone.now())
            if coverageEnd > timeNow and foundNext == 0:
                highlightRow = raceCount
                bold = "**"
                foundNext = 1
            else:
                bold = ""

            schedTable += bold + coverageStart.strftime("%-m/%-d") + bold + "|" + bold + session.race.shortname + bold + "|" + bold + coverageStart.strftime("%I:%M%p").lstrip("0").lower() + bold + "|" + bold + session.channel.name + bold + "\n"

        schedTable += "\nAll times Eastern"

        # logit("[Sidebar] Built schedule table.")

        styles = sub.stylesheet()
        oldCSS = styles.stylesheet
        newCSS = styles.stylesheet

        highlightCSS = ".side table tr:nth-of-type(" + str(highlightRow) + ") td {"
        newCSS = re.sub("\.side table tr:nth-of-type\(\d+\) td \{", highlightCSS, newCSS, flags=re.S)

        old = oldCSS.split("\n")
        new = newCSS.split("\n")

        if newCSS != oldCSS:
            logit("[Sidebar] Stylesheet update required!")
            sub.stylesheet.update(newCSS)
            logit("[Sidebar] Stylesheet updated.")


        sidebar = re.sub("### 2018 IndyCar Schedule.*All times Eastern", schedTable, sidebar, flags=re.S)
        if (sidebar != oldSidebar):
            logit("[Sidebar] Sidebar update required!\n")
            sub.mod.update(description=sidebar)
        # else:
        #     logit("[Sidebar] No change required.\n")
        self.update_progress(100, 100)
        return 1


class UploadLiveriesTask(JobtasticTask):
    herd_avoidance_timeout = 60
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):
        subreddits	= [settings.SUBREDDIT]
        user_agent	= ("/r/IndyCar crew chief v1.9.1 by /u/Badgerballs")
        logit(str(os.getcwd()))
        message = ""
        percentage = float(0)
        subPercentage = float(80/len(subreddits))

        r = praw.Reddit(user_agent=user_agent)
        r.refresh_access_information()

        if r.user == None:
            message += "Failed to log in. Something went wrong!\n"
            logit(message)
        else:
            message += "Logged in to reddit as " + str(r.user)
            logit(message)
        self.update_progress(20, 100)


        for sub in subreddits:
            r.upload_image(sub, "./static/liveries.png", "liveries")
            percentage = percentage + float(subPercentage/5)
            self.update_progress(percentage, 100)

            sub = r.get_subreddit(sub)
            percentage = percentage + float(subPercentage/5)
            self.update_progress(percentage, 100)

            css = r.get_stylesheet(sub)['stylesheet']
            percentage = percentage + float(subPercentage/5)
            self.update_progress(percentage, 100)

            r.set_stylesheet(sub, css)
            percentage = percentage + float(subPercentage/5)
            self.update_progress(percentage, 100)

            subsettings = sub.get_settings()
            percentage = percentage + float(subPercentage/5)
            self.update_progress(percentage, 100)

            message += "Updated /r/" + str(sub) + "\n"

        self.update_progress(percentage, 100)

        return message


class GenerateLiveriesTask(JobtasticTask):
    herd_avoidance_timeout = 120
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    # def generateLiveries(self, stamp, **kwargs):
    def calculate_result(self, stamp, **kwargs):
        offline 	= False
        image_dir	= "liveries"
        width		= 189
        height		= 42
        sprite_rows = 11
        sprite_cols = 9

        percentage = float(0)
        message = ""

        liveryXPath = '//img[@class="driver-car-image"]/@src'
        driverXPath = '//div[@class="driver-listing__driver-profile"]/a/@href'

        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        for i in xrange(1, 99):
            shutil.copy("blank.png", image_dir + "/" + str(i) + ".png")

        page = requests.get("https://www.indycar.com/Drivers/")
        tree = html.fromstring(page.content)
        driverPageList = tree.xpath(driverXPath)

        self.update_progress(5, 100)

        driverPercentage = float(95.0 / float(len(driverPageList)))
        driverList = Driver.objects.order_by('last', 'first').filter(active=1)

        for driverPage in driverPageList:
            page = requests.get("http://www.indycar.com" + driverPage)
            tree = html.fromstring(page.content)

            imgsrc = tree.xpath(liveryXPath)[0]
            imgsrc = imgsrc.rsplit('?', -1)[0]
            filename = re.sub('[-_].*\.png', '.png', imgsrc.rsplit('/', -1)[-1])

            lastName = driverPage.rsplit('-', -1)[-1]

            msg = driverPage + " as filename: " + filename + ".  Last name: " + lastName
            try:
                if Driver.objects.filter(active=1).get(last__icontains=lastName):
                    msg = "ACTIVE: " + msg
                r = requests.get(imgsrc + "?h=42", stream=True)
                if r.status_code == 200:
                    with open(image_dir + "/" + filename, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                del r
            except:
                msg = "INACTIVE: " + msg

            slack_message('slack/liveryDriver.slack', {'driver': msg})


            percentage = percentage + driverPercentage
            self.update_progress(percentage, 100)

            message += "Filename: " + filename + "\n"

        dirList=sorted(os.listdir(image_dir))

        message += ", ".join(dirList)

        images = [Image.open(image_dir + "/" + fname) for fname in dirList]
        master_width = width * sprite_cols
        master_height = height * sprite_rows

        master = Image.new(mode='RGBA', size=(master_width, master_height), color=(0,0,0,0))

        try:
            for y in xrange(0, sprite_rows):
                for x in xrange(0, sprite_cols):
                    master.paste(images[ (y*sprite_cols) + x ], (x*width,y*height))
        except:
            x = "This is horrible code."

        master.save('./static/liveries.png')

        self.update_progress(percentage, 100)

        return message
