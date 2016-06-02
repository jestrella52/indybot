import requests
import pycurl
import shutil
import django
import praw
import re
import os

from PIL import Image
from lxml import html
from time import sleep
from celery import Celery

os.environ['DJANGO_SETTINGS_MODULE'] = 'indybot.settings'
django.setup()

from django_slack import slack_message

from jobtastic import JobtasticTask

from .models import Country, Driver

celery = Celery('tasks', backend='amqp', broker='amqp://guest@localhost//')


class UploadLiveriesTask(JobtasticTask):
    herd_avoidance_timeout = 60
    cache_duration = 0

    significant_kwargs = [
        ('stamp', str),
    ]

    def calculate_result(self, stamp, **kwargs):
        subreddits	= ["indycar", "badgerballs"]
        user_agent	= ("/r/IndyCar Livery bot v0.9.1 by /u/Badgerballs")
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
