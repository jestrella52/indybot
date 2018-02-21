import operator
import datetime
import django
import pytz
import time
import praw
import json
import sys
import re
import os

from PIL import Image

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import (login as auth_login, authenticate)
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
from django.views.generic.edit import UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.utils import timezone

from django.shortcuts import render_to_response

from django_slack import slack_message

from celery import states
from celery.result import AsyncResult

from manager.tasks import GenerateLiveriesTask, RedditThreadTask
from manager.tasks import UpdateRedditSidebarTask, UploadLiveriesTask
from manager.tasks import TweetTask, RedditPostsTask

from .forms import BaseNestedFormset, BaseNestedModelForm, CautionForm, ChannelForm
from .forms import CountryForm, CourseForm, DriverForm, EventForm, PostForm, RaceForm
from .forms import RedditAccountForm, SeasonForm, SessionForm, SessionTypeForm, TweetForm

from .models import Caution, CautionDriver, CautionReason, Channel, Country
from .models import Course, Driver, Post, Race, RedditAccount, Result, ResultType
from .models import Season, Session, SessionType, Start, Tweet, Type

from .social import removeTweet

from .support import logit

from .racethread import compile, raceInfo, winnerList

def nestedformset_factory(parent_model, model, nested_formset,
                          form=BaseNestedModelForm,
                          formset=BaseNestedFormset, fk_name=None,
                          fields=None, exclude=None, extra=3,
                          can_order=False, can_delete=True,
                          max_num=None, formfield_callback=None,
                          widgets=None, validate_max=False,
                          localized_fields=None, labels=None,
                          help_texts=None, error_messages=None,
                          min_num=None, validate_min=None):
    kwargs = {
        'form': form,
        'formfield_callback': formfield_callback,
        'formset': formset,
        'extra': extra,
        'can_delete': can_delete,
        'can_order': can_order,
        'fields': fields,
        'exclude': exclude,
        'max_num': max_num,
            'widgets': widgets,
            'validate_max': validate_max,
            'localized_fields': localized_fields,
            'labels': labels,
            'help_texts': help_texts,
            'error_messages': error_messages,
    }

    if kwargs['fields'] is None:
        kwargs['fields'] = [
            field.name
            for field in model._meta.local_fields
        ]

    if django.VERSION >= (1, 7):
        kwargs.update({
            'min_num': min_num,
            'validate_min': validate_min,
        })

    NestedFormSet = inlineformset_factory(
        parent_model,
        model,
        **kwargs
    )
    NestedFormSet.nested_formset_class = nested_formset

    return NestedFormSet


@login_required
def index(request):
    circuitList = Course.objects.order_by('id')
    countryList = Country.objects.order_by('id')
    driverList = Driver.objects.order_by('id')
    raceList = Race.objects.order_by('id')
    seasonList = Season.objects.order_by('id')
    postList = Post.objects.order_by('id')
    resultQualCount = Result.objects.filter(type_id=1).count()
    resultRaceCount = Result.objects.filter(type_id=2).count()
    cautionCount = Caution.objects.count()

    template = loader.get_template('index.html')
    context = {
        'title': "IndyBot",
        'driverList': driverList,
        'circuitList': circuitList,
        'raceList': raceList,
        'seasonList': seasonList,
        'countryList': countryList,
        'postList': postList,
        'resultQualCount': resultQualCount,
        'resultRaceCount': resultRaceCount,
        'cautionCount': cautionCount,
    }
    return HttpResponse(template.render(context, request))


@login_required
def driver_list(request):
    driverList = Driver.objects.order_by('last', 'first')
    template = loader.get_template('driverList.html')
    context = {
        'title': "All Drivers",
        'driverList': driverList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def driver_list_active(request):
    driverList = Driver.objects.order_by('last', 'first').filter(active=1)
    template = loader.get_template('driverList.html')
    context = {
        'title': "Active Drivers",
        'driverList': driverList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def driver_list_inactive(request):
    driverList = Driver.objects.order_by('last', 'first').filter(active=0)
    template = loader.get_template('driverList.html')
    context = {
        'title': "Inactive Drivers",
        'driverList': driverList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def driver_list_current(request):
    currentYear = datetime.date.today().year
    driverList = Driver.objects.order_by('last', 'first').filter(Q(active=1) | Q(result__race__season__year=currentYear)).distinct()

    template = loader.get_template('driverList.html')
    context = {
        'title': "Drivers - Current Season",
        'driverList': driverList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def driver_list_shared(request):
    driverList = Driver.objects.filter(number__gte=1).order_by('number')
    numberList = driverList.values_list('number', flat=True)
    dupeNumberList = []

    for number in numberList:
        count = 0
        for x in range(0, len(numberList)):
            if numberList[x] == number:
                count = count + 1

        if count > 1 and not number in dupeNumberList:
            dupeNumberList.append(number)

    driverList = Driver.objects.filter(number__in=dupeNumberList).order_by('number')

    template = loader.get_template('driverList.html')
    context = {
        'title': "Drivers - Shared Rides",
        'driverList': driverList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def driver_toggleActive(request, driver_id):
    driver = get_object_or_404(Driver, pk=driver_id)
    if driver.active:
        driver.active = False
    else:
        driver.active = True
    driver.save()
    return HttpResponse(driver.active)


@login_required
def start_list(request):
    startList = Start.objects.order_by('id')
    template = loader.get_template('startList.html')
    context = {
        'startList': startList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def type_list(request):
    typeList = Type.objects.order_by('id')
    template = loader.get_template('typeList.html')
    context = {
        'typeList': typeList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def resultType_list(request):
    resultTypeList = ResultType.objects.order_by('id')
    template = loader.get_template('resultTypeList.html')
    context = {
        'resultTypeList': resultTypeList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def country_list(request):
    countryList = Country.objects.order_by('name')
    template = loader.get_template('countryList.html')
    context = {
        'countryList': countryList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def channel_list(request):
    channelList = Channel.objects.order_by('name')
    template = loader.get_template('channelList.html')
    context = {
        'channelList': channelList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def season_list(request):
	seasonList = Season.objects.order_by('year')
	template = loader.get_template('seasonList.html')
	context = {
		'seasonList': seasonList,
	}
	return HttpResponse(template.render(context, request))


@login_required
def sessiontype_list(request):
    sessionTypeList = SessionType.objects.order_by('name')
    template = loader.get_template('sessionTypeList.html')
    context = {
        'sessionTypeList': sessionTypeList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def post_list(request):
    postList = Post.objects.order_by('-publish_time')
    template = loader.get_template('postList.html')
    context = {
        'postList': postList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def post_list_pending(request):
    postList = Post.objects.order_by('publish_time')
    postList = postList.filter(publish_time__gt=datetime.datetime.now())
    template = loader.get_template('postList.html')
    context = {
        'postList': postList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def race_list(request, season=None):

    seasonObj = None
    sessionTypeValue = SessionType.objects.get(name="Race")

    if season:
        raceList = Race.objects.filter(season=season)
        seasonObj= Season.objects.get(id=season)
        title = "Races - " + str(seasonObj.year) + " Season"
    else:
        raceList = Race.objects.all()
        title = "All Races"

    template = loader.get_template('raceList.html')

    for i in xrange(len(raceList)):
        itemResults = Result.objects.filter(race_id=raceList[i].id)
        sentinelTime = timezone.make_aware(datetime.datetime(raceList[i].season.year, 12, 31, 23, 59, 59))

        gotStartTime = False
        try:
            raceSession = Session.objects.get(race_id=raceList[i].id, type_id=sessionTypeValue)
            if raceSession.tvstarttime:
                raceList[i].startTime = raceSession.tvstarttime
            else:
                raceList[i].startTime = sentinelTime
            gotStartTime = True
        except Session.DoesNotExist:
            raceList[i].startTime = sentinelTime

        if gotStartTime:
            try:
                raceList[i].channel = raceSession.channel.name
            except:
                pass

        if itemResults.filter(type_id=1).count() == 0:
            raceList[i].qualResultStyle = 'style="color:lightgrey"'
        if itemResults.filter(type_id=2).count() == 0:
            raceList[i].raceResultStyle = 'style="color:lightgrey"'

    if season:
        raceList = sorted(raceList, key=operator.attrgetter('startTime'))
    else:
        raceList = sorted(raceList, key=operator.attrgetter('startTime'), reverse=True)

    context = {
        'title': title,
        'raceList': raceList,
        'seasonObj': seasonObj,
    }
    return HttpResponse(template.render(context, request))


@login_required
def country_create(request):
    if request.method == "POST":
        form = CountryForm(request.POST)
        if form.is_valid():
            country = form.save()
            return redirect('country_list')
    else:
        form = CountryForm()

    template = loader.get_template('countryEdit.html')
    context = {
        'title': "New Country",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def channel_create(request):
    if request.method == "POST":
        form = ChannelForm(request.POST)
        if form.is_valid():
            channel = form.save()
            return redirect('channel_list')
    else:
        form = ChannelForm()

    template = loader.get_template('channelEdit.html')
    context = {
        'title': "New Channel",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def season_create(request):
    if request.method == "POST":
        form = SeasonForm(request.POST)
        if form.is_valid():
            season = form.save()
            return redirect('season_list')
    else:
        form = SeasonForm()

    template = loader.get_template('seasonEdit.html')
    context = {
        'title': "New Season",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def sessiontype_create(request):
    if request.method == "POST":
        form = SessionTypeForm(request.POST)
        if form.is_valid():
            sessionType = form.save()
            return redirect('sessiontype_list')
    else:
        form = SessionTypeForm()

    template = loader.get_template('sessionTypeEdit.html')
    context = {
        'title': "New Session Type",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def post_create(request):
    author = get_object_or_404(RedditAccount, owner_id=request.user.id)
    if request.method == "POST":
        form = PostForm(request.POST, user=request.user, initial={'author': author.id})
        if form.is_valid():
            post = form.save(commit=False)
            post.modified_time = datetime.datetime.now()
            if not request.user.is_staff:
                post.author_id = author.id
            slack_message('slack/postCreateRich.slack', {
                'author': author,
                'post': post,
            },
                [{
                    'title': post.title,
                    'text': post.body,
                },])
            post = form.save()
            return redirect('post_list')
    else:
        form = PostForm(user=request.user, initial={'author': author})

    template = loader.get_template('postEdit.html')
    context = {
        'title': "New Post",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = get_object_or_404(RedditAccount, owner_id=request.user.id)
    if request.method == "POST":
        form = PostForm(request.POST, user=request.user, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.modified_time = datetime.datetime.now(pytz.timezone('US/Eastern'))
            if post.publish_time > post.modified_time:
                post.submission = None
            if not request.user.is_staff:
                post.author_id = author.id
            post = form.save()
            return redirect('post_list')
    else:
        form = PostForm(user=request.user, instance=post)

    template = loader.get_template('postEdit.html')
    context = {
        'title': "Edit Post",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def country_delete(request, country_id):
    try:
        country = Country.objects.get(id=country_id)
        country.delete()
        return redirect('country_list')
    except:
        noop = ""


@login_required
def sessiontype_delete(request, sessiontype_id):
    try:
        sessiontype = SessionType.objects.get(id=sessiontype_id)
        sessiontype.delete()
        return redirect('sessiontype_list')
    except:
        noop = ""


@login_required
def channel_delete(request, channel_id):
    try:
        channel = Channel.objects.get(id=channel_id)
        channel.delete()
        return redirect('channel_list')
    except:
        noop = ""


@login_required
def season_delete(request, season_id):
    try:
        season = Season.objects.get(id=season_id)
        season.delete()
        return redirect('season_list')
    except:
        noop = ""


@login_required
def country_edit(request, country_id):
    country = get_object_or_404(Country, pk=country_id)
    if request.method == "POST":
        form = CountryForm(request.POST, instance=country)
        if form.is_valid():
            country = form.save()
            return redirect('country_list')
    else:
        form = CountryForm(instance=country)

    template = loader.get_template('countryEdit.html')
    context = {
        'title': "Edit Country",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def sessiontype_edit(request, sessiontype_id):
    sessiontype = get_object_or_404(SessionType, pk=sessiontype_id)
    if request.method == "POST":
        form = SessionTypeForm(request.POST, instance=sessiontype)
        if form.is_valid():
            sessiontype = form.save()
            return redirect('sessiontype_list')
    else:
        form = SessionTypeForm(instance=sessiontype)

    template = loader.get_template('sessionTypeEdit.html')
    context = {
        'title': "Edit Session Type",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def session_edit(request, race_id):

    sessions = Session.objects.filter(race_id=race_id).order_by('starttime')
    session_data = [{'type': s.type,
                     'name': s.name,
                     'starttime': s.starttime,
                     'endtime': s.endtime,
                     'posttime': s.posttime,
                     'channel': s.channel,
                     'tvstarttime': s.tvstarttime,
                     'tvendtime': s.tvendtime,
                     }
                    for s in sessions]

    if request.method == "POST":
        SessionFormSet = formset_factory(SessionForm, extra=0)
        event_form = EventForm(request.POST, race_id=race_id)
        session_formset = SessionFormSet(request.POST)

        if event_form.is_valid() and session_formset.is_valid():
            new_sessions = []

            for session_form in session_formset:
                session_type      = session_form.cleaned_data.get('type')
                session_name      = session_form.cleaned_data.get('name')
                session_startTime = session_form.cleaned_data.get('starttime')
                session_endTime   = session_form.cleaned_data.get('endtime')
                session_postTime  = session_form.cleaned_data.get('posttime')
                session_channel   = session_form.cleaned_data.get('channel')
                session_tvStartTime = session_form.cleaned_data.get('tvstarttime')
                session_tvEndTime   = session_form.cleaned_data.get('tvendtime')

                if race_id and session_type and session_name and session_startTime and session_endTime:
                    new_sessions.append(Session(race_id=race_id,
                                                type=session_type,
                                                name=session_name,
                                                starttime=session_startTime,
                                                endtime=session_endTime,
                                                posttime=session_postTime,
                                                channel=session_channel,
                                                tvstarttime=session_tvStartTime,
                                                tvendtime=session_tvEndTime
                                                ))
                try:
                    with transaction.atomic():
                        Session.objects.filter(race_id=race_id).delete()
                        Session.objects.bulk_create(new_sessions)

                        # messages.success(request, "Sessions updated.")
                except IntegrityError as e:
                    logit(str(e))
                    # messages.error(request, "Error saving sessions.")
                    return redirect(reverse('session_edit', race_id=race_id))

    else:
        SessionFormSet = formset_factory(SessionForm, extra=1)
        event_form = EventForm(race_id=race_id)
        session_formset = SessionFormSet(initial=session_data)

    template = loader.get_template('eventSessionsEdit.html')
    context = {
        'title': "Edit Sessions",
        'event_form': event_form,
        'session_formset': session_formset,
    }
    return HttpResponse(template.render(context, request))


@login_required
def season_edit(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    if request.method == "POST":
        form = SeasonForm(request.POST, instance=season)
        if form.is_valid():
            season = form.save()
            return redirect('season_list')
    else:
        form = SeasonForm(instance=season)

    template = loader.get_template('seasonEdit.html')
    context = {
        'title': "Edit Season",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def channel_edit(request, channel_id):
    channel = get_object_or_404(Channel, pk=channel_id)
    if request.method == "POST":
        form = ChannelForm(request.POST, instance=channel)
        if form.is_valid():
            channel = form.save()
            return redirect('channel_list')
    else:
        form = ChannelForm(instance=channel)

    template = loader.get_template('channelEdit.html')
    context = {
        'title': "Edit Channel",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def circuit_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            circuit = form.save()
            return redirect('circuit_list')
    else:
        form = CourseForm()

    template = loader.get_template('circuitEdit.html')
    context = {
        'title': "New Circuit",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def race_create(request):
    if request.method == "POST":
        form = RaceForm(request.POST)
        if form.is_valid():
            race = form.save()
            return redirect('race_list')
    else:
        form = RaceForm()

    template = loader.get_template('raceEdit.html')
    context = {
        'title': "New Race",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def race_edit(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    CautionFormSet = formset_factory(CautionForm)
    if request.method == "POST":
        form = RaceForm(request.POST, instance=race)
        if form.is_valid():
            race = form.save()
            return redirect('race_list')
    else:
        form = RaceForm(instance=race)

    template = loader.get_template('raceEdit.html')
    context = {
        'title': "Edit Race",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def circuit_edit(request, circuit_id):
    circuit = get_object_or_404(Course, pk=circuit_id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=circuit)
        if form.is_valid():
            circuit = form.save()
            return redirect('circuit_list')
    else:
        form = CourseForm(instance=circuit)

    template = loader.get_template('circuitEdit.html')
    context = {
        'title': "Edit Circuit",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def circuit_delete(request, circuit_id):
    try:
        circuit = Course.objects.get(id=circuit_id)
        circuit.delete()
        return redirect('circuit_list')
    except:
        noop = ""


@login_required
def race_delete(request, race_id):
    try:
        race = Race.objects.get(id=race_id)
        race.delete()
        return redirect('race_list')
    except:
        noop = ""


@login_required
def cautiondriver_delete(request, cautiondriver_id, race_id):
    try:
        cautiondriver = CautionDriver.objects.get(id=cautiondriver_id)
        cautiondriver.delete()
        return redirect('/race/' + str(race_id) + '/caution/edit/')
    except:
        noop = ""


@login_required
def caution_delete(request, caution_id, race_id):
    try:
        cautiondrivers = CautionDriver.objects.get(caution=caution_id)
        cautiondrivers.delete()
        caution = Caution.objects.get(id=caution_id)
        caution.delete()
        return redirect('/race/' + str(race_id) + '/caution/edit/')
    except:
        noop = ""


@login_required
def driver_create(request):
    if request.method == "POST":
        form = DriverForm(request.POST)
        if form.is_valid():
            driver = form.save()
            return redirect('driver_list')
    else:
        form = DriverForm()

    template = loader.get_template('driverEdit.html')
    context = {
        'title': "New Driver",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def tweet_list(request):
    tweetList = Tweet.objects.order_by('-publish_time')
    template = loader.get_template('tweetList.html')
    context = {
        'tweetList': tweetList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def tweet_create(request):
    author = get_object_or_404(RedditAccount, owner_id=request.user.id)
    if request.method == "POST":
        form = TweetForm(request.POST, initial={'author': author.id})
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.author = author
            tweet = form.save()
            return redirect('tweet_list')
    else:
        form = TweetForm()

    template = loader.get_template('tweetEdit.html')
    context = {
        'title': "New Tweet",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def tweet_edit(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id)
    if request.method == "POST":
        form = TweetForm(request.POST, instance=tweet)
        if form.is_valid():
            tweet = form.save()
            return redirect('tweet_list')
    else:
        form = TweetForm(instance=tweet)

    template = loader.get_template('tweetEdit.html')
    context = {
        'title': "Edit Tweet",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@staff_member_required
def tweet_delete(request, tweet_id):
    try:
        tweet = Tweet.objects.get(id=tweet_id)
        if tweet.tid:
            if removeTweet(str(tweet.tid)):
                tweet.deleted = True
                tweet.save()
        else:
            tweet.delete()

        return redirect('tweet_list')
    except Exception as e:
        logit(str(e))



@staff_member_required
def redditAccount_create(request):
    if request.method == "POST":
        form = RedditAccountForm(request.POST)
        if form.is_valid():
            redditAccount = form.save()
            return redirect('redditAccount_list')
    else:
        form = RedditAccountForm()

    template = loader.get_template('redditAccountEdit.html')
    context = {
        'title': "New Reddit Account Mapping",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def driver_edit(request, driver_id):
    driver = get_object_or_404(Driver, pk=driver_id)
    if request.method == "POST":
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            driver = form.save()
            return redirect('driver_list')
    else:
        form = DriverForm(instance=driver)

    template = loader.get_template('driverEdit.html')
    context = {
        'title': "Edit Driver",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


class EditCautionsView(UpdateView):
    model = Race
    fields = '__all__'

    def get_template_names(self):
        return ['cautionEdit.html']

    def get_form_class(self):
        return nestedformset_factory(
            Race,
            Caution,
            nested_formset=inlineformset_factory(Caution, CautionDriver, fields='__all__')
        )

    def get_success_url(self):
        return reverse('race_list')


@staff_member_required
def redditAccount_edit(request, redditaccount_id):
    redditAccount = get_object_or_404(RedditAccount, pk=redditaccount_id)
    if request.method == "POST":
        form = RedditAccountForm(request.POST, instance=redditAccount)
        if form.is_valid():
            redditAccount = form.save()
            return redirect('redditAccount_list')
    else:
        form = RedditAccountForm(instance=redditAccount)

    template = loader.get_template('redditAccountEdit.html')
    context = {
        'title': "Edit Reddit Account Mapping",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@staff_member_required
def redditAccount_delete(request, redditaccount_id):
    try:
        redditAccount = RedditAccount.objects.get(id=redditaccount_id)
        redditAccount.delete()
        return redirect('redditAccount_list')
    except:
        noop = ""


@login_required
def driver_delete(request, driver_id):
    try:
        driver = Driver.objects.get(id=driver_id)
        driver.delete()
        return redirect('driver_list')
    except:
        noop = ""


@login_required
def post_delete(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        post.delete()
        return redirect('post_list')
    except:
        noop = ""


@login_required
def results_edit(request, race_id, resulttype_id):

    race = Race.objects.get(id=race_id)
    resultTypeName = ResultType.objects.get(id=resulttype_id)
    currentYear = datetime.date.today().year
    if (race.season.year == currentYear):
        # Get all drivers marked active OR who have a Result object for the current season.
        activeDrivers = Driver.objects.filter(Q(active=1) | Q(result__race__season__year=currentYear)).distinct()
    else:
        activeDrivers = Driver.objects.order_by('last', 'first')

    driverPositions = []
    positions = []

    try:
        resultList = Result.objects.filter(race_id=race_id).filter(type_id=resulttype_id).order_by('position')
    except Result.DoesNotExist:
        resultList = None

    for i in range(1,34):
        try:
            driverPositions.append(resultList[i-1].driver_id)
        except IndexError:
            driverPositions.append(0)

    positionNumbers = range(1,34)

    positions = zip(positionNumbers, driverPositions)
    template = loader.get_template('resultEdit.html')

    context = {
        'race': race,
        'resultList': resultList,
        'activeDrivers': activeDrivers,
        'resultTypeName': resultTypeName,
        'positions': positions,
    }

    return HttpResponse(template.render(context, request))


@login_required
def results_update(request, race_id, resulttype_id):
    output = "<table>"
    output = output + "<tr><th>Position</th><th>Driver ID</th><th>ResultType</th><th>Race</th></tr>"
    race = get_object_or_404(Race, pk=race_id)
    resultType = get_object_or_404(ResultType, pk=resulttype_id)
    for result in request.POST:
        if request.POST[result] == "0":
            continue

        if len(result.split("_")) == 3:
            position = int(result.split("_")[2])
            driver = int(request.POST[result])

            try:
                item = Result.objects.get(type_id=resultType.id, race_id=race.id, position=position)
                item.driver_id = driver
                item.save()
            except Result.DoesNotExist:
                r = Result(type_id=resultType.id, race_id=race.id, position=position, driver_id=driver)
                r.save()

    return redirect('race_list')


@login_required
def circuit_list(request):
    circuitList = Course.objects.order_by('name')
    template = loader.get_template('circuitList.html')
    context = {
        'circuitList': circuitList,
    }
    return HttpResponse(template.render(context, request))


@staff_member_required
def tasks(request, task_name=None):
    redir = False
    ts = str(time.time())

    if task_name == "RedditThreadTask":
        RedditThreadTask.delay_or_fail(stamp=ts)
        redir = True
    elif task_name == "TweetTask":
        TweetTask.delay_or_fail(stamp=ts)
        redir = True
    elif task_name == "RedditPostsTask":
        RedditPostsTask.delay_or_fail(stamp=ts)
        redir = True
    elif task_name == "UpdateRedditSidebarTask":
        UpdateRedditSidebarTask.delay_or_fail(stamp=ts)
        redir = True
    elif task_name == "UploadLiveriesTask":
        UploadLiveriesTask.delay_or_fail(stamp=ts)
        redir = True
    elif task_name == "GenerateLiveriesTask":
        GenerateLiveriesTask.delay_or_fail(stamp=ts)
        redir = True

    if redir:
        return redirect('tasks')
    else:
        template = loader.get_template('tasks.html')
        context = {}
        return HttpResponse(template.render(context, request))


@staff_member_required
def redditAccount_list(request):
    redditAccountList = RedditAccount.objects.order_by('handle')
    template = loader.get_template('redditAccountList.html')
    context = {
        'redditAccountList': redditAccountList,
    }
    return HttpResponse(template.render(context, request))


@login_required
def password_change_done():
    template = loader.get_template('passwordChangeDone.html')
    return HttpResponse(template.render(request))


@login_required
def liveries_upload(request):

    ts = str(time.time())
    result = UploadLiveriesTask.delay_or_fail(stamp=ts)

    template = loader.get_template('liveriesShow.html')
    context = {
        'task': "upload",
        'task_id': result.task_id,
        'message': "Uploading Liveries Spritesheet...",
    }
    return HttpResponse(template.render(context, request))


@login_required
def liveries_show(request):

    filename = "./static/liveries.png"

    if os.path.isfile(filename):
        message = "Liveries spritesheet last generated: " + str(datetime.datetime.fromtimestamp(os.path.getmtime(filename)))
    else:
        message = "No liveries spritesheet found.  Please generate one."

    template = loader.get_template('liveriesShow.html')
    context = {
        'title': "Current Liveries",
        'message': message
    }
    return HttpResponse(template.render(context, request))


@login_required
def sidebar_update(request):
    ts = str(time.time())
    result = UpdateRedditSidebarTask.delay_or_fail(stamp=ts)

    template = loader.get_template('sidebarUpdate.html')
    context = {'title': "Sidebar Update"}
    return HttpResponse(template.render(context, request))


@login_required
def liveries_regenerate(request):

    ts = str(time.time())
    result = GenerateLiveriesTask.delay_or_fail(stamp=ts)

    template = loader.get_template('liveriesShow.html')
    context = {
        'task': "regenerate",
        'task_id': result.task_id,
        'message': "Regenerating Liveries Spritesheet..."
    }
    return HttpResponse(template.render(context, request))


@login_required
def race_thread(request, race_id):
    thread = compile(race_id, output="html")

    template = loader.get_template('raceThread.html')
    context = {
        'thread': thread
    }
    return HttpResponse(template.render(context, request))


@login_required
def output(request):
    upcomingPosts = Session.objects.filter(submission_id__isnull=True).filter(posttime__isnull=False).order_by('posttime')
    ts = str(time.time())
    result = RedditThreadTask.delay_or_fail(stamp=ts)

    template = loader.get_template('output.html')
    context = {
        'output': upcomingPosts
    }
    return HttpResponse(template.render(context, request))


@csrf_exempt
def task(request, task_id):

    """Returns task status and result in JSON format."""
    result = AsyncResult(task_id)
    state, retval = result.state, result.result
    response_data = {'id': task_id, 'status': state, 'result': retval}
    if state in states.EXCEPTION_STATES:
        traceback = result.traceback
        response_data.update({'result': safe_repr(retval),
                              'exc': get_full_cls_name(retval.__class__),
                              'traceback': traceback})
    return JsonResponse({'task': response_data})


def login(request):
    _message = 'Please sign in'
    if request.method == 'POST':
        _username = request.POST['username']
        _password = request.POST['password']
        user = authenticate(username=_username, password=_password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                _message = 'Your account is not activated'
        else:
            _message = 'Invalid login, please try again.'

    template = loader.get_template('login.html')
    context = {'message': _message}
    return HttpResponse(template.render(context, request))
