from django import forms

from .models import Country, Course, Driver

class CountryForm(forms.ModelForm):

    class Meta:
        model = Country
        fields = ('name', 'code', 'iso')


class CourseForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = ('name', 'location', 'length', 'url', 'fastyear', 'fastlap', 'fastdriver', 'gps', 'shortname', 'country', 'type')


class DriverForm(forms.ModelForm):

    class Meta:
        model = Driver
        fields = ('last', 'first', 'twitter', 'number', 'rookie', 'country', 'active')
