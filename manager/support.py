import datetime
import inspect

from django.conf import settings

def logit(message):
    stamp = datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S")
    try:
        caller = inspect.stack()[1][3]
    except:
        caller = "unknown"

    with open(settings.INDYBOT_LOGFILE, "a") as myfile:
        myfile.write(stamp + " - " + caller + " - " + str(message) + "\n")
