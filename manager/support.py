from django.conf import settings

def logit(message):
    with open(settings.INDYBOT_LOGFILE, "a") as myfile:
        myfile.write(message + "\n")
