from django import forms
from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib.auth.models import User
from django.forms.models import BaseInlineFormSet, inlineformset_factory, ModelForm
from crispy_forms.helper import FormHelper

from crispy_forms.layout import Fieldset, HTML, Layout, Row, Submit
from crispy_forms.bootstrap import Alert, AppendedText, Div, Field
from crispy_forms.bootstrap import PrependedText, StrictButton, TabHolder, Tab

from .models import Caution, CautionDriver, CautionReason, Channel, Country
from .models import Course, Driver, Post, Race, RedditAccount, Season, Session
from .models import SessionType, Tweet

class BaseNestedModelForm(ModelForm):

    def has_changed(self):

        return (
            super(BaseNestedModelForm, self).has_changed() or
            self.nested.has_changed()
        )


class BaseNestedFormset(BaseInlineFormSet):

    def add_fields(self, form, index):

        # allow the super class to create the fields as usual
        super(BaseNestedFormset, self).add_fields(form, index)

        form.nested = self.nested_formset_class(
            instance=form.instance,
            data=form.data if self.is_bound else None,
            prefix='%s-%s' % (
                form.prefix,
                self.nested_formset_class.get_default_prefix(),
            ),
        )

    def is_valid(self):

        result = super(BaseNestedFormset, self).is_valid()

        if self.is_bound:
            # look at any nested formsets, as well
            for form in self.forms:
                result = result and form.nested.is_valid()

        return result

    def save(self, commit=True):

        result = super(BaseNestedFormset, self).save(commit=commit)

        for form in self:
            form.nested.save(commit=commit)

        return result


class ChannelForm(forms.ModelForm):

    class Meta:
        model = Channel
        fields = ('name',)


class CautionForm(forms.ModelForm):

    class Meta:
        model = Caution
        fields = ('startLap', 'endLap', 'reason', 'description')


class EventForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.race_id = kwargs.pop('race_id', None)
        super(EventForm, self).__init__(*args, **kwargs)

        self.fields['race_id'] = forms.IntegerField(initial=self.race_id,
                                                    widget=forms.HiddenInput())

        # self.helper = FormHelper(self)
        # self.helper.layout=Layout(
        #     Submit('submit', u'Submit', css_class='btn btn-xxx btn-success'),
        # )


class SessionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SessionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.form_tag = False

        # self.fields['starttime'].widget = DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"})
        # self.fields['endtime'].widget   = DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"})
        # self.fields['posttime'].widget  = DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"})

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(Field('type', autofocus=True), css_class="col-md-3"),
                    Div(Field('name'), css_class="col-md-3"),
                    Div(Field('posttime', placeholder="YYYY-MM-DD HH:MM"), css_class="col-md-3"),
                    Div(Field('channel'), css_class="col-md-2"),
                    # Div(PrependedText('post', ''), css_class="col-md-1"),
                    Div(HTML("""<div class="form-group"><label class="control-label">&nbsp;</label><div class="controls"><a class="btn btn-danger" href="javascript:void(0)"><strong>X</strong></a></div></div>"""), align="right", css_class="col-md-1"),
                css_class="row"),
                Div(
                    Div(Field('starttime', placeholder="YYYY-MM-DD HH:MM"), css_class="col-md-3"),
                    Div(Field('endtime', placeholder="YYYY-MM-DD HH:MM"), css_class="col-md-3"),
                    Div(Field('tvstarttime', placeholder="YYYY-MM-DD HH:MM"), css_class="col-md-3"),
                    Div(Field('tvendtime', placeholder="YYYY-MM-DD HH:MM"), css_class="col-md-3"),
                    # Div(Field('starttime'), css_class="col-md-4"),
                    # Div(Field('endtime'), css_class="col-md-4"),
                    # Div(Field('posttime'), css_class="col-md-4"),
                css_class="row"),
            css_class="well well-lg session-form")
        )
    class Meta:
        model = Session
        fields = ('type', 'name', 'starttime', 'endtime', 'channel', 'posttime', 'tvstarttime', 'tvendtime')
        labels = {
            'starttime': "Start Time",
            'endtime': "End Time",
            'posttime': "Post Time",
            'tvstarttime': "TV Broadcast Start",
            'tvendtime': "TV Broadcast End",
        }


class CautionDriverForm(forms.ModelForm):

    class Meta:
        model = CautionDriver
        fields = ('driver',)


class CountryForm(forms.ModelForm):

    class Meta:
        model = Country
        fields = ('name', 'code', 'iso')


class SeasonForm(forms.ModelForm):

    class Meta:
        model = Season
        fields = ('year', 'seriesname', 'races', 'champion', 'rookie', 'fanfav')


class SessionTypeForm(forms.ModelForm):

    class Meta:
        model = SessionType
        fields = ('name',)


class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Div(
                Div(Field('name', autofocus=True), css_class="col-md-3"),
                Div(Field('location'), css_class="col-md-3"),
                Div(Field('country'), css_class="col-md-3"),
                Div(Field('gps'), css_class="col-md-3"),
                css_class="row"
            ),
            Div(
                Div(AppendedText('length', "mi."), css_class="col-md-2"),
                Div(Field('type'), css_class="col-md-2"),
                Div(Field('shortname'), css_class="col-md-2"),
                Div(PrependedText('twitter', "@"), css_class="col-md-3"),
                Div(Field('url'), css_class="col-md-3"),
                css_class="row"
            ),
            Fieldset("Track Record",
                Div(AppendedText('fastlap', "mph"), css_class="col-md-4"),
                Div(Field('fastdriver'), css_class="col-md-4"),
                Div(Field('fastyear'), css_class="col-md-4"),
            ),
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )

    class Meta:
        model = Course
        fields = ('name', 'location', 'length', 'url', 'twitter', 'fastyear', 'fastlap', 'fastdriver', 'gps', 'shortname', 'country', 'type')
        labels = {
            'url': "Circuit URL",
            'fastyear': "Year",
            'fastlap': "Speed",
            'fastdriver': "Driver",
            'gps': "GPS Coordinates",
            'shortname': "Short Name",
            'twitter': "Twitter Handle"
        }


class DriverForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DriverForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Div(
                Div(Field('last', autofocus=True), css_class="col-md-3"),
                Div(Field('first'), css_class="col-md-3"),
                Div(Field('country'), css_class="col-md-3"),
                Div(PrependedText('twitter', "@"), css_class="col-md-3"),
                css_class="row"
            ),
            Div(
                Div(Field('rookie'), css_class="col-md-3"),
                Div(Field('number'), css_class="col-md-3"),
                Div(Field('dob', placeholder="YYYY-MM-DD"), css_class="col-md-3"),
                Div(Field('died', placeholder="YYYY-MM-DD"), css_class="col-md-3"),
                css_class="row"
            ),
            Div(Div(Field('active'), css_class="col-md-3"), css_class="row"),
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )
    class Meta:
        model = Driver
        fields = ('last', 'first', 'dob', 'died', 'twitter', 'number', 'rookie', 'country', 'active')
        labels = {
            'last': "Last Name",
            'first': "First Name",
            'dob': "Born",
            'died': "Died",
            'twitter': "Twitter Handle",
            'rookie': "Rookie Year",
            'active': "Active?"
        }


class RaceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RaceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            TabHolder(
                Tab('Pre-Race Information',
                    Div(
                        Div(Field('season', autofocus=True), css_class="col-md-3"),
                        Div(Field('title'), css_class="col-md-3"),
                        Div(Field('course'), css_class="col-md-3"),
                        Div(Field('url'), css_class="col-md-3"),
                        css_class="row"
                    ),
                    Div(
                        Div(Field('laps'), css_class="col-md-2"),
                        Div(Field('rowsize'), css_class="col-md-2"),
                        Div(Field('start'), css_class="col-md-2"),
                        Div(Field('shortname'), css_class="col-md-2"),
                        Div(Field('channel'), css_class="col-md-2"),
                        Div(Field('hashtag'), css_class="col-md-2"),
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
            ),
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )

    class Meta:
        model = Race
        fields = ('season', 'title', 'shortname', 'laps', 'practice', 'coverage', 'green', 'endcoverage', 'channel', 'hashtag', 'url', 'urlrr', 'submission', 'subpractice', 'subpostrace', 'urlrace', 'urlpractice', 'urlpostrace', 'rowsize', 'course', 'start', 'yellowflags', 'yellowlaps', 'duration', 'speedavg', 'speedpole', 'leadchanges', 'margin')
        labels = {
            'shortname': "Short Name",
            'laps': "Number of Laps",
            'practice': "First Practice Starts",
            'coverage': "Broadcast Starts",
            'green': "Green Flag Flies",
            'endcoverage': "Broadcast Ends",
            'channel': "TV Channel",
            'hashtag': "Hashtag",
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


class TweetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TweetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Div(
                Div(AppendedText('text', "0", autofocus=True), css_class="col-md-12"),
                css_class="row"
            ),
            Div(
                Div(Field('publish_time'), css_class="col-md-4"),
                Div(HTML("""<div class="form-group"><label class="control-label">&nbsp;</label><div class="controls"><a class="btn btn-primary btn-now col-md-1" href="javascript:void(0)">Now</a></div></div>""")),
                css_class="row"
            ),
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )

    class Meta:
        model = Tweet
        fields = ('text', 'publish_time')
        labels = {
            'text': "Tweet Text",
            'publish_time': "Publish At",
        }
        widgets = {
            'publish_time': DateTimePicker(options={"format": "YYYY-MM-DD HH:mm:ss"})
        }


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
