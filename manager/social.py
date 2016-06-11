import os
import django
import twitter

from .support import logit

os.environ['DJANGO_SETTINGS_MODULE'] = 'indybot.settings'
django.setup()

from django.conf import settings


def getTwitterAPI():
    return twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                       consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                       access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
                       access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET)


def removeTweet(tid=False):
    logit("getting api")
    api = getTwitterAPI()
    logit("got api")
    try:
        logit("Removing status: " + str(tid))
        status = api.DestroyStatus(tid)
        logit("delete status: " + str(status))
        return True
    except Exception as e:
        raise
