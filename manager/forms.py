from django import forms
from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Row
from crispy_forms.bootstrap import Alert, AppendedText, Div, Field, TabHolder, Tab

from .models import Country, Course, Driver, Post, Race, RedditAccount

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
        fields = ('last', 'first', 'dob', 'died', 'twitter', 'number', 'rookie', 'country', 'active')


class RaceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RaceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab('Pre-Race Information',
                    Div(
                        Div(Field('title'), css_class="col-md-4"),
                        Div(Field('course'), css_class="col-md-4"),
                        Div(Field('url'), css_class="col-md-4"),
                        css_class="row"
                    ),
                    Div(
                        Div(Field('laps'), css_class="col-md-3"),
                        Div(Field('rowsize'), css_class="col-md-3"),
                        Div(Field('start'), css_class="col-md-3"),
                        Div(Field('channel'), css_class="col-md-3"),
                        css_class="row"
                    ),
                    Fieldset("Dates and Times",
                        Div(
                            Div(Field('practice', placeholder="YYYY-MM-DD HH:MM"), css_class="col-md-3"),
                            Div(Field('coverage', placeholder="YYYY-MM-DD HH:MM"), css_class="col-md-3"),
                            Div(Field('green', placeholder="YYYY-MM-DD HH:MM"), css_class="col-md-3"),
                            Div(Field('endcoverage', placeholder="YYYY-MM-DD HH:MM"), css_class="col-md-3"),
                            css_class="row"
                        ),
                    ),
                    css_class="fade in"
                ),
                Tab('Post-Race Statistics',
                    'urlrr',
                    Div(
                        Div(AppendedText('duration', "seconds"), css_class="col-md-4"),
                        Div(Field('yellowflags'), css_class="col-md-4"),
                        Div(Field('yellowlaps'), css_class="col-md-4"),
                        css_class="row"
                    ),
                    Div(
                        Div(AppendedText('speedavg', "mph"), css_class="col-md-3"),
                        Div(AppendedText('speedpole', "mph"), css_class="col-md-3"),
                        Div(AppendedText('margin', "seconds"), css_class="col-md-3"),
                        Div(Field('leadchanges'), css_class="col-md-3"),
                        css_class="row"
                    ),
                    css_class="fade"
                ),
                Tab('Reddit Internals',
                    Alert(content="<strong>Wait a second!</strong> &nbsp;Changing anything on this page could make IndyBot do some weird shit. &nbsp; So... &nbsp; Don't.", css_class="alert-danger"),
                    Fieldset("Practice Thread",
                        Div(
                            Div(Field('subpractice'), css_class="col-md-2"),
                            Div(Field('urlpractice'), css_class="col-md-10"),
                            css_class="row"
                        ),
                    ),
                    Fieldset("Race Thread",
                        Div(
                            Div(Field('submission'), css_class="col-md-2"),
                            Div(Field('urlrace'), css_class="col-md-10"),
                            css_class="row"
                        ),
                    ),
                    Fieldset("Post-Race Thread",
                        Div(
                            Div(Field('subpostrace'), css_class="col-md-2"),
                            Div(Field('urlpostrace'), css_class="col-md-10"),
                            css_class="row"
                        ),
                    ),
                    css_class="fade"
                )
            )
        )

    class Meta:
        model = Race
        fields = ('title', 'laps', 'practice', 'coverage', 'green', 'endcoverage', 'channel', 'url', 'urlrr', 'submission', 'subpractice', 'subpostrace', 'urlrace', 'urlpractice', 'urlpostrace', 'rowsize', 'course', 'start', 'yellowflags', 'yellowlaps', 'duration', 'speedavg', 'speedpole', 'leadchanges', 'margin')
        labels = {
            'laps': "Number of Laps",
            'practice': "First Practice Starts",
            'coverage': "Broadcast Starts",
            'green': "Green Flag Flies",
            'endcoverage': "Broadcast Ends",
            'channel': "TV Channel",
            'url': "URL for the Race's Website",
            'urlrr': "This Race's URL on Racing-Reference",
            'rowsize': "Row Size",
            'course': "Circuit",
            'start': "Start Method",
            'yellowflags': "Number of Caution Periods",
            'yellowlaps': "Total Laps Under Caution",
            'duration': "Race Duration",
            'speedavg': "Average Speed",
            'speedpole': "Pole Speed",
            'leadchanges': "Number of Lead Changes",
            'margin': "Margin of Victory",
            'subpractice': "SubID",
            'urlpractice': "URL",
            'submission': "SubID",
            'urlrace': "URL",
            'subpostrace': "SubID",
            'urlpostrace': "URL"
        }


class RedditAccountForm(forms.ModelForm):

    class Meta:
        model = RedditAccount
        fields = ('handle', 'owner')


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'body', 'sticky', 'publish_time', 'author')
        widgets = {
            'title': forms.TextInput(attrs={'size': 80}),
            'body': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        }

    def __init__(self, *args, **kwargs):
        published = kwargs.pop('published', None)
        user = kwargs.pop('user', None)
        super(PostForm, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['author'].required = False
            self.fields['author'].widget.attrs['disabled'] = 'disabled'
            self.fields['author'].widget = forms.HiddenInput()
