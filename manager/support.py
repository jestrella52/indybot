
def logit(message):
    with open("/tmp/bot.log", "a") as myfile:
        myfile.write(message + "\n")
