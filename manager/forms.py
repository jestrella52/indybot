from django import forms
from bootstrap3_datetime.widgets import DateTimePicker

from .models import Country, Course, Driver, Post, Race

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


class RaceForm(forms.ModelForm):

    class Meta:
        model = Race
        fields = ('title', 'coverage', 'green', 'channel', 'url', 'submission', 'rowsize', 'course', 'start')


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'body', 'sticky', 'publish_time')
        widgets = {
            'title': forms.TextInput(attrs={'size': 80}),
            'body': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        }
