import datetime
import pycurl
import shutil
import praw
import sys
import re
import os

from PIL import Image

from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import (login as auth_login, authenticate)
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse

from .forms import CountryForm, CourseForm, DriverForm, PostForm, RaceForm, RedditAccountForm, SeasonForm
from .models import Country, Course, Driver, Post, Race, RedditAccount, Result, ResultType, Season, Start, Type


class Page:
	def __init__(self):
		self.contents = ''

	def body_callback(self, buf):
		self.contents = self.contents + buf


@login_required
def index(request):
    circuitList = Course.objects.order_by('id')
    countryList = Country.objects.order_by('id')
    driverList = Driver.objects.order_by('id')
    raceList = Race.objects.order_by('id')
    seasonList = Season.objects.order_by('id')
    postList = Post.objects.order_by('id')

    template = loader.get_template('index.html')
    context = {
        'title': "IndyBot",
        'driverList': driverList,
        'circuitList': circuitList,
        'raceList': raceList,
        'seasonList': seasonList,
        'countryList': countryList,
        'postList': postList,
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
def season_list(request):
	seasonList = Season.objects.order_by('year')
	template = loader.get_template('seasonList.html')
	context = {
		'seasonList': seasonList,
	}
	return HttpResponse(template.render(context, request))


@login_required
def post_list(request):
    postList = Post.objects.order_by('publish_time')
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

    if season:
        raceList = Race.objects.order_by('green')
        raceList = raceList.filter(season = season)
    else:
        raceList = Race.objects.order_by('-green')

    template = loader.get_template('raceList.html')

    for i in xrange(len(raceList)):
        qualResultStyle = ''
        raceResultStyle = ''

        itemResults = Result.objects.filter(race_id=raceList[i].id)

        if itemResults.filter(type_id=1).count() == 0:
            raceList[i].qualResultStyle = 'style="color:lightgrey"'
        if itemResults.filter(type_id=2).count() == 0:
            raceList[i].raceResultStyle = 'style="color:lightgrey"'

    context = {
        'raceList': raceList,
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
def post_create(request):
    author = get_object_or_404(RedditAccount, owner_id=request.user.id)
    if request.method == "POST":
        form = PostForm(request.POST, user=request.user, initial={'author': author.id})
        if form.is_valid():
            post = form.save(commit=False)
            post.modified_time = datetime.datetime.now()
            if not request.user.is_staff:
                post.author_id = author.id
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
            post.modified_time = datetime.datetime.now()
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
    if (race.green.year == datetime.date.today().year):
        activeDrivers = Driver.objects.order_by('last', 'first').filter(active=1)
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
    # for r in resultList:
    #     driverPositions.append(r.driver_id)

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
            # if item.driver_id != driver:
            #     item.
            # newItem = Result.objects.update_or_create(driver_id=driver, defaults={'type_id': resultType.id, 'race_id': race.id, 'position': position})

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
def liveries_regenerate(request):

    offline 	= False
    image_dir	= "liveries"
    width		= 189
    height		= 42
    sprite_rows = 11
    sprite_cols = 9

    message = ""

    for i in xrange(1, 99):
        shutil.copy("blank.png", image_dir + "/" + str(i) + ".png")

    c = pycurl.Curl()
    page = Page()
    c.setopt(pycurl.URL, "http://www.indycar.com/Drivers")
    c.setopt(c.WRITEFUNCTION, page.body_callback)
    c.perform()
    c.close()

    driverURLBase = "http://www.indycar.com/Series/IndyCar-Series/"
    driverURLName = []

    lines = page.contents.split('\n')
    driverLinkPattern = re.compile('^\s+\<a href=\"/Series/IndyCar-Series/([a-zA-Z\-]+)\"')
    liveryURLPattern = re.compile('^\s+\<img src=\"(http://[a-z0-9]+\.cloudfront\.net/~/media/IndyCar/Cars/2016/IndyCar-Series/Liveries/\w+/[0-9a-zA-Z\-]+\.png)')

    for line in lines:
    	match = driverLinkPattern.match(line)
    	if match:
    		driverURLName.append(match.group(1))

    for name in driverURLName:
    	message += "Checking:" + name + " - " + driverURLBase + name + "\n"
    	c = pycurl.Curl()
    	page = Page()
    	c.setopt(pycurl.URL, driverURLBase + name)
    	c.setopt(c.WRITEFUNCTION, page.body_callback)
    	c.perform()
    	c.close()

    	lines = page.contents.split('\n')
    	for line in lines:
    		match = liveryURLPattern.match(line)
    		if match:
    			filename = match.group(1).rsplit('/', -1)[-1]
    			filename = re.sub('[-_].*\png', '.png', filename)

    			fp = open(image_dir + "/" + filename, "wb")
    			c2 = pycurl.Curl()
    			c2.setopt(pycurl.URL, match.group(1) + "?h=42")
    			c2.setopt(c.WRITEDATA, fp)
    			c2.perform()
    			c2.close()
    			fp.close()

        message += "Filename: " + filename + "\n"

    dirList=sorted(os.listdir(image_dir))
    # dirList = sorted(dirList, key=lambda x: (int(re.sub('\D','',x)),x))

    message += ", ".join(dirList)

    images = [Image.open(image_dir + "/" + fname) for fname in dirList]
    master_width = width * sprite_cols
    master_height = height * sprite_rows

    master = Image.new(mode='RGBA', size=(master_width, master_height), color=(0,0,0,0))

    try:
    	for y in xrange(0, sprite_rows):
    		for x in xrange(0, sprite_cols):
    			master.paste(images[ (y*sprite_cols) + x ], (x*width,y*height))
    except:
    	x = "This is horrible code."

    master.save('./static/liveries.png')

    return redirect('liveries_show')


@login_required
def liveries_upload(request):

    subreddits	= ["indycar", "badgerballs"]
    user_agent	= ("/r/IndyCar Livery bot v0.9.1 by /u/Badgerballs")
    message = ""

    r = praw.Reddit(user_agent=user_agent)
    r.refresh_access_information()
    if r.user == None:
        message += "Failed to log in. Something went wrong!<br>"
    else:
        message += "Logged in to reddit as " + str(r.user)

    for sub in subreddits:
    	r.upload_image(sub, "./static/liveries.png", "liveries")
    	sub = r.get_subreddit(sub)
        css = r.get_stylesheet(sub)['stylesheet']
        r.set_stylesheet(sub, css)
        settings = sub.get_settings()
        # message += ", ".join(sub.get_settings())
        message += "  ---  Updated /r/" + str(sub)

    template = loader.get_template('liveriesShow.html')
    context = {
        'title': "Current Liveries",
        'message': message,
    }
    return HttpResponse(template.render(context, request))



@login_required
def liveries_show(request):

    filename = "./static/liveries.png"

    if os.path.isfile(filename):
        message = "Liveries spritesheet last generated: " + str(datetime.datetime.fromtimestamp(os.path.getmtime(filename)))

    template = loader.get_template('liveriesShow.html')
    context = {
        'title': "Current Liveries",
        'message': message
    }
    return HttpResponse(template.render(context, request))


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
