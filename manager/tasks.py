import datetime
import requests
import twitter
import pycurl
import shutil
import django
import praw
import time
import re
import os

from PIL import Image
from lxml import html
from time import sleep
from celery import Celery
from celery.schedules import crontab

os.environ['DJANGO_SETTINGS_MODULE'] = 'indybot.settings'
django.setup()

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django_slack import slack_message

from jobtastic import JobtasticTask

from .models import Country, Driver, Post, Race, RedditAccount, Tweet

celery = Celery('tasks', backend='amqp', broker='amqp://guest@localhost//')

if settings.INDYBOT_ENV == "PROD":
    celery.conf.update(
        CELERYBEAT_SCHEDULE = {
            'update-sidebar': {
                'task': 'manager.tasks.UpdateRedditSidebarTask',
                'schedule': crontab(hour='*', minute='5'),
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
if settings.INDYBOT_ENV == "DEVEL":
    celery.conf.update(
        CELERYBEAT_SCHEDULE = {
            'check-tweets': {
                'task': 'manager.tasks.TweetTask',
                'schedule': datetime.timedelta(seconds=30),
                'kwargs': {'stamp': str(time.time())},
            }
        }
    )

posterCredits  = "***\n\nIndyBot submitted this post on behalf of /u/"
indybotCredits = "***\n\n^(Questions, comments, or hate mail regarding IndyBot should be directed to /u/BadgerBalls.)\n"


def logit(message):
    with open("/tmp/bot.log", "a") as myfile:
        myfile.write(message + "\n")


def bumpLog():
    with open("/tmp/bot.log", "a") as myfile:
        myfile.write("\n\n")


class TweetTask(JobtasticTask):
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
            except:
                logit("TWITTER LOGIN FAILED")

        self.update_progress(100, 100)
        return 1


class RedditPostsTask(JobtasticTask):
    herd_avoidance_timeout = 20
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):
        logit("===============================================================")
        logit("starting up")
        subreddit = "badgerballs"
        user_agent	= ("/r/IndyCar crew chief v1.9.1 by /u/Badgerballs")

        posts = Post.objects.filter(submission=None).filter(Q(publish_time__lte=timezone.now())).prefetch_related('author')
        logit(str(len(posts)) + " posts in queue.")

        if len(posts) > 0:
            r = praw.Reddit(user_agent=user_agent)
            r.refresh_access_information()

            if r.user == None:
                logit("Failed to log in. Something went wrong!")
            else:
                logit("Logged in to reddit as " + str(r.user))

            for post in posts:
                logit("- - - - - - - - - - - - - - -")
                postBody = post.body

                if post.credit:
                    postBody = postBody + "\n\n" + posterCredits + str(post.author) + "\n"

                postBody += indybotCredits
                submission = r.submit(subreddit, post.title, text=postBody)

                if post.sticky:
                    submission.sticky()

                post.submission = submission.id
                post.save()

                logit(post.title + ", by " + str(post.author))
                logit("Scheduled for: " + str(post.publish_time))
                timePub = timezone.make_naive(post.publish_time)
                timeNow = timezone.make_naive(timezone.now())
                logit("Adjusted time: " + str(timePub))
                logit("Current time: " + str(timeNow))
                if (timeNow >= timePub):
                    logit ("POSTING!")

        self.update_progress(100, 100)

        return 1


class UpdateRedditSidebarTask(JobtasticTask):
    herd_avoidance_timeout = 60
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):

        subreddits = ["badgerballs"]
        user_agent	= ("/r/IndyCar crew chief v1.9.1 by /u/Badgerballs")

        # with open("/tmp/bot.log", "a") as myfile:
        #     myfile.write(str(os.getcwd()) + "\n")

        message = ""
        percentage = float(0)
        subPercentage = float(80/len(subreddits))

        r = praw.Reddit(user_agent=user_agent)
        r.refresh_access_information()

        if r.user == None:
            message += "Failed to log in. Something went wrong!\n"
            # with open("/tmp/bot.log", "a") as myfile:
            #     myfile.write(message + "\n")
        else:
            message += "Logged in to reddit as " + str(r.user)
            # with open("/tmp/bot.log", "a") as myfile:
            #     myfile.write(message + "\n")
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


        for subreddit in subreddits:
            settings = r.get_settings(subreddit)
            oldSidebar = settings['description']
            sidebar = oldSidebar

            start = timezone.make_aware(datetime.datetime(datetime.date.today().year, 1, 1))
            end = timezone.make_aware(datetime.datetime(datetime.date.today().year, 12, 31))

            races = Race.objects.order_by('green').filter(green__gte=start).filter(green__lte=end)

            foundNext = 0
            highlightRow = 0
            raceCount = 0

            schedTable  = "### 2016 IndyCar Schedule\n\n"
            schedTable += "**Date**|**Course**|**Time**|**TV**\n"
            schedTable += ":---|:---|:---|:---\n"

            for race in races:
                raceCount = raceCount + 1
                coverageStart = timezone.make_naive(race.coverage)
                coverageEnd = timezone.make_naive(race.endcoverage)
                timeNow = timezone.make_naive(timezone.now())
                if coverageEnd > timeNow and foundNext == 0:
                    highlightRow = raceCount
                    bold = "**"
                    foundNext = 1
                else:
                    bold = ""

                schedTable += bold + coverageStart.strftime("%-m/%-d") + bold + "|" + bold + race.shortname + bold + "|" + bold + coverageStart.strftime("%I:%M%p").lstrip("0").lower() + bold + "|" + bold + race.channel + bold + "\n"

            schedTable += "\nAll times Eastern"


            stylesheet = r.get_stylesheet(subreddit)
            newCSS = stylesheet['stylesheet']
            oldCSS = stylesheet['stylesheet']

            highlightCSS = ".side table tr:nth-of-type(" + str(highlightRow) + ") td {"
            newCSS = re.sub("\.side table tr:nth-of-type\(\d+\) td \{", highlightCSS, newCSS, flags=re.S)

            old = oldCSS.split("\n")
            new = newCSS.split("\n")

            # with open("/tmp/bot.log", "a") as myfile:
            #     for i in range(0, 10):
            #         myfile.write("-------\n")
            #         myfile.write(old[i] + "\n")
            #         myfile.write(new[i] + "\n")

            if newCSS != oldCSS:
                # with open("/tmp/bot.log", "a") as myfile:
                #     myfile.write("Stylesheet update required!\n")
                r.set_stylesheet(subreddit, '')
                r.set_stylesheet(subreddit, newCSS)

            # with open("/tmp/bot.log", "a") as myfile:
            #     myfile.write(schedTable + "\n")

            sidebar = re.sub("### 2016 IndyCar Schedule.*All times Eastern", schedTable, sidebar, flags=re.S)
            if (sidebar != oldSidebar):
                # with open("/tmp/bot.log", "a") as myfile:
                #     myfile.write("Sidebar update required!\n")
                settings = r.update_settings(r.get_subreddit(subreddit), description=sidebar)
            # else:
                # with open("/tmp/bot.log", "a") as myfile:
                #     myfile.write("No change required.\n")
        self.update_progress(100, 100)
        return 1


class UploadLiveriesTask(JobtasticTask):
    herd_avoidance_timeout = 60
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):
        subreddits	= ["indycar", "badgerballs"]
        user_agent	= ("/r/IndyCar crew chief v1.9.1 by /u/Badgerballs")
        with open("/tmp/bot.log", "a") as myfile:
            myfile.write(str(os.getcwd()))
        message = ""
        percentage = float(0)
        subPercentage = float(80/len(subreddits))

        r = praw.Reddit(user_agent=user_agent)
        r.refresh_access_information()

        if r.user == None:
            message += "Failed to log in. Something went wrong!\n"
            with open("/tmp/bot.log", "a") as myfile:
                myfile.write(message)
        else:
            message += "Logged in to reddit as " + str(r.user)
            with open("/tmp/bot.log", "a") as myfile:
                myfile.write(message)
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

            settings = sub.get_settings()
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

        page = requests.get("http://www.indycar.com/Drivers")
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
