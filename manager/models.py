from __future__ import unicode_literals

from datetime import date

from django.db import models
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Country(models.Model):
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=3)
    iso = models.CharField(max_length=10)

    class Meta:
        db_table = "country"
        ordering = ["name"]
    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Driver(models.Model):
    last = models.CharField(max_length=20)
    first = models.CharField(max_length=20)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    active = models.BooleanField(default=False)
    twitter = models.CharField(max_length=30, blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    rookie = models.IntegerField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    died = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "driver"
        ordering = ["last", "first"]
    def __str__(self):
        return self.last + ", " + self.first


class Season(models.Model):
    year = models.IntegerField()
    seriesname = models.CharField(max_length=100)
    races = models.IntegerField()
    champion = models.ForeignKey(Driver, related_name="season_champion", blank=True, null=True)
    rookie = models.ForeignKey(Driver, related_name="season_rookie", blank=True, null=True)
    fanfav = models.ForeignKey(Driver, related_name="season_fanfav", blank=True, null=True)


    class Meta:
        db_table = "season"
    def __str__(self):
        return str(self.year)


class Start(models.Model):
    type = models.CharField(max_length=10)

    class Meta:
        db_table = "start"
    def __str__(self):
        return self.type


class Type(models.Model):
    type = models.CharField(max_length=20)

    class Meta:
        db_table = "type"
    def __str__(self):
        return self.type


@python_2_unicode_compatible
class Course(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    type = models.ForeignKey(Type)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    length = models.FloatField()
    url = models.CharField(max_length=200)
    fastdriver = models.ForeignKey(Driver, blank=True, null=True)
    fastyear = models.IntegerField(blank=True, null=True)
    fastlap = models.FloatField(blank=True, null=True)
    gps = models.CharField(max_length=30)
    shortname = models.CharField(max_length=20)

    class Meta:
        db_table = "course"
        ordering = ["name"]
    def __str__(self):
        return self.name


class Race(models.Model):
    title = models.CharField(max_length=70)
    shortname = models.CharField(max_length=30, blank=True, null=True)
    course = models.ForeignKey(Course)
    practice = models.DateTimeField(blank=True, null=True)
    coverage = models.DateTimeField(blank=True, null=True)
    green = models.DateTimeField(blank=True, null=True)
    endcoverage = models.DateTimeField(blank=True, null=True)
    channel = models.CharField(max_length=15, blank=True, null=True)
    url = models.CharField(max_length=100, blank=True, null=True)
    urlrr = models.CharField(max_length=100, blank=True, null=True)
    submission = models.CharField(max_length=10, blank=True, null=True)
    subpractice = models.CharField(max_length=10, blank=True, null=True)
    subpostrace = models.CharField(max_length=10, blank=True, null=True)
    urlpractice = models.CharField(max_length=200, blank=True, null=True)
    urlrace = models.CharField(max_length=200, blank=True, null=True)
    urlpostrace = models.CharField(max_length=200, blank=True, null=True)
    grid = models.CharField(max_length=150, blank=True, null=True)
    rowsize = models.IntegerField(default=2)
    laps = models.IntegerField(blank=True, null=True)
    yellowflags = models.IntegerField(blank=True, null=True)
    yellowlaps = models.IntegerField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    speedavg = models.FloatField(blank=True, null=True)
    speedpole = models.FloatField(blank=True, null=True)
    leadchanges = models.IntegerField(blank=True, null=True)
    margin = models.FloatField(blank=True, null=True)
    start = models.ForeignKey(Start)
    season = models.ForeignKey(Season, on_delete=models.PROTECT, null=True)
    hashtag = models.CharField(max_length=20, blank=True, null=True)

    @property
    def in_the_past(self):
        if date.today() >= self.green.date():
            return True
        return False

    class Meta:
        db_table = "race"
    def __str__(self):
        return self.title


class CautionReason(models.Model):
    reason = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = "caution_reason"
        ordering = ["reason"]
    def __str__(self):
        return self.reason


class Caution(models.Model):
    race = models.ForeignKey(Race, on_delete=models.PROTECT)
    reason = models.ForeignKey(CautionReason)
    description = models.CharField(max_length=30, blank=True, null=True)
    startLap = models.IntegerField()
    endLap = models.IntegerField()

    class Meta:
        db_table = "caution"
        ordering = ["race"]


class CautionDriver(models.Model):
    caution = models.ForeignKey(Caution, on_delete=models.PROTECT)
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT)

    class Meta:
        db_table = "caution_driver"
        ordering = ["caution"]


class ResultType(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        db_table = "resulttype"
    def __str__(self):
        return self.name


class Result(models.Model):
    race = models.ForeignKey(Race, null=True)
    type = models.ForeignKey(ResultType)
    driver = models.ForeignKey(Driver)
    position = models.IntegerField()

    class Meta:
        db_table = "result"


class Winner(models.Model):
    driver = models.ForeignKey(Driver)
    course = models.ForeignKey(Course)
    year = models.IntegerField()

    class Meta:
        db_table = "winner"


class RedditAccount(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    handle = models.CharField(max_length=20)

    class Meta:
        db_table = "redditaccount"
    def __str__(self):
        return self.handle


class Post(models.Model):
    title = models.CharField(max_length=300)
    body = models.TextField()
    sticky = models.BooleanField(default=False)
    submission = models.CharField(max_length=10, blank=True, null=True)
    publish_time = models.DateTimeField(blank=False, null=False)
    modified_time = models.DateTimeField(blank=False, null=False)
    credit = models.BooleanField(default=True)
    author = models.ForeignKey(RedditAccount)

    class Meta:
        db_table = "post"
    def __str__(self):
        return self.title
