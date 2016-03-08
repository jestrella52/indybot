from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Country(models.Model):
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=3)
    iso = models.CharField(max_length=10)

    class Meta:
        db_table = "country"
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

    class Meta:
        db_table = "driver"
    def __str__(self):
        return self.last + ", " + self.first


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
    def __str__(self):
        return self.name


class Race(models.Model):
    title = models.CharField(max_length=70)
    course = models.ForeignKey(Course)
    coverage = models.DateTimeField(blank=True, null=True)
    green = models.DateTimeField(blank=True, null=True)
    channel = models.CharField(max_length=10, blank=True, null=True)
    url = models.CharField(max_length=100, blank=True, null=True)
    submission = models.CharField(max_length=10, blank=True, null=True)
    grid = models.CharField(max_length=150, blank=True, null=True)
    rowsize = models.IntegerField(default=2)
    start = models.ForeignKey(Start)

    class Meta:
        db_table = "race"
    def __str__(self):
        return self.title


class ResultType(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        db_table = "resulttype"
    def __str__(self):
        return self.name


class Result(models.Model):
    # course = models.ForeignKey(Course, null=True)
    race = models.ForeignKey(Race, null=True)
    # races = models.ManyToManyField(Race, related_name='results')
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
