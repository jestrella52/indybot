import logging
from django.conf import settings

def logit(message):
    logging.basicConfig(level=logging.INFO,
                        filename=settings.INDYBOT_LOGFILE,
                        format='%(asctime)s %(message)s')
    logging.info(str(message))
    # with open(settings.INDYBOT_LOGFILE, "a") as myfile:
    #     myfile.write(message + "\n")
