from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CountryForm
from .models import Country, Course, Driver, Race, Result, ResultType, Start, Type

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def country_edit(request, country_id):
    return HttpResponse("You're looking at country %s." % country_id)

def driver_edit(request, driver_id):
    return HttpResponse("You're looking at driver %s." % driver_id)

def start_edit(request, start_id):
    return HttpResponse("You're looking at start %s." % start_id)

def driver_list(request):
    driverList = Driver.objects.order_by('last', 'first')
    template = loader.get_template('driverList.html')
    context = {
        'title': "All Drivers",
        'driverList': driverList,
    }
    return HttpResponse(template.render(context, request))

def driver_list_active(request):
    driverList = Driver.objects.order_by('last', 'first').filter(active=1)
    template = loader.get_template('driverList.html')
    context = {
        'title': "Active Drivers",
        'driverList': driverList,
    }
    return HttpResponse(template.render(context, request))

def driver_list_inactive(request):
    driverList = Driver.objects.order_by('last', 'first').filter(active=0)
    template = loader.get_template('driverList.html')
    context = {
        'title': "Inactive Drivers",
        'driverList': driverList,
    }
    return HttpResponse(template.render(context, request))

def start_list(request):
    startList = Start.objects.order_by('id')
    template = loader.get_template('startList.html')
    context = {
        'startList': startList,
    }
    return HttpResponse(template.render(context, request))

def type_list(request):
    typeList = Type.objects.order_by('id')
    template = loader.get_template('typeList.html')
    context = {
        'typeList': typeList,
    }
    return HttpResponse(template.render(context, request))

def resultType_list(request):
    resultTypeList = ResultType.objects.order_by('id')
    template = loader.get_template('resultTypeList.html')
    context = {
        'resultTypeList': resultTypeList,
    }
    return HttpResponse(template.render(context, request))

def country_list(request):
    countryList = Country.objects.order_by('name')
    template = loader.get_template('countryList.html')
    context = {
        'countryList': countryList,
    }
    return HttpResponse(template.render(context, request))

def race_list(request):
    raceList = Race.objects.order_by('-green')
    template = loader.get_template('raceList.html')
    context = {
        'raceList': raceList,
    }
    return HttpResponse(template.render(context, request))
    # return HttpResponse("You're looking at race %s." % race_id)

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

def country_delete(request, country_id):
    try:
        country = Country.objects.get(id=country_id)
        country.delete()
        return redirect('country_list')
    except:
        noop = ""


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
        'title': "New Country",
        'form': form,
    }
    return HttpResponse(template.render(context, request))


def results_edit(request, race_id, resulttype_id):

    race = Race.objects.get(id=race_id)
    resultTypeName = ResultType.objects.get(id=resulttype_id)
    activeDrivers = Driver.objects.filter(active=1).order_by('last', 'first')
    driverPositions = []
    positions = []

    try:
        resultList = Result.objects.filter(race_id=race_id).order_by('position')
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

    return HttpResponse(output)

def circuit_list(request):
    circuitList = Course.objects.order_by('name')
    template = loader.get_template('circuitList.html')
    context = {
        'circuitList': circuitList,
    }
    return HttpResponse(template.render(context, request))
