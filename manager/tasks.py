import requests
import pycurl
import shutil
import re
import os

from PIL import Image
from lxml import html
from time import sleep
from celery import Celery

from jobtastic import JobtasticTask

os.environ['DJANGO_SETTINGS_MODULE'] = 'indybot.settings'
celery = Celery('tasks', backend='amqp', broker='amqp://guest@localhost//')


# class Page:
#     def __init__(self):
#         self.contents = ''
#
#     def body_callback(self, buf):
#         self.contents = self.contents + buf


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

        for driverPage in driverPageList:
            page = requests.get("http://www.indycar.com" + driverPage)
            tree = html.fromstring(page.content)

            imgsrc = tree.xpath(liveryXPath)[0]
            imgsrc = imgsrc.rsplit('?', -1)[0]
            filename = re.sub('[-_].*\.png', '.png', imgsrc.rsplit('/', -1)[-1])

            r = requests.get(imgsrc + "?h=42", stream=True)
            if r.status_code == 200:
                with open(image_dir + "/" + filename, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            del r

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
