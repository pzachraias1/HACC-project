from json import dumps
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect
import uuid
import requests

from django.template.loader import render_to_string

from .models import Url, IP_Adresses, Verification_Table
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime


# Create your views here.


@login_required(login_url='login')
def hello(request):
    host = request.META['HTTP_HOST']
    context = {
        'hostname' : host,
        'name' : 'zeek'
    }
    return render(request, 'index.html', context)


def status_method(url):
    try:
        r = requests.head(url)
        status_code = r.status_code
        return status_code
    except requests.RequestException:
        return "No server"


@login_required(login_url='login')
def shorten(request):
    host = request.META['HTTP_HOST']
    if request.method == 'POST':
        lURL = request.POST['link']
        if "https://" not in lURL:
            lURL = "https://" + lURL + "/"
        pw = request.POST['pass']
        if ".gov" not in lURL:
            return HttpResponse("error")
        if status_method(lURL) == "No Server":
            return HttpResponse("No Server")
        if status_method(lURL) != 200:
            lURL = request.POST['link']
            lURL = "https://www." + lURL + "/"
            if status_method(lURL) != 200:
                return HttpResponse("Bad")
        if Url.objects.filter(longLink=lURL).exists():
            return HttpResponse("sCode " + host + "/" + Url.objects.get(longLink=lURL).shortCode)
        sCode = str(uuid.uuid4())[:5]
        shortUrl = Url(longLink=lURL, shortCode=sCode)
        shortUrl.save()
        if pw != "":
            veriObj = Verification_Table(shortCode=shortUrl, password=pw)
            shortUrl.verification = True
            shortUrl.save()
            veriObj.save()
        return HttpResponse(host + "/" + sCode)


def forward(request, pk):
    long_url = Url.objects.get(shortCode=pk)
    if long_url.verification is True:
        context = {
            'pk': pk
        }
        return render(request, 'redirect_verification.html', context)
    long_url.clicks += 1
    long_url.save()
    ip = get_client_ip(request)
    # ip = "204.210.114.78"
    response = requests.get(f'https://ipapi.co/{ip}/json/').json()
    city = response.get('city')
    region = response.get('region')
    country = response.get('country')
    longitude = response.get('longitude')
    latitude = response.get('latitude')
    ip_origin = IP_Adresses(shortCode=long_url, ip_address=ip, city=city, region=region, country=country,
                            longitude=longitude,
                            latitude=latitude)
    ip_origin.save()
    return redirect(long_url.longLink)


@login_required(login_url='login')
def manage_view(request):
    host = request.META['HTTP_HOST']
    queryset = Url.objects.all()
    ipset = IP_Adresses.objects.all()
    verificationTable = Verification_Table.objects.all()

    iplist = []
    idlist = []
    visitList = []
    passwordList = []
    passwordID = []
    locationList = []

    for x in ipset:
        iplist.append(x.ip_address)
        idlist.append(x.shortCode.pk)
        hr = str(x.visitedDate.astimezone().hour)
        min = str(x.visitedDate.astimezone().minute)
        sec = str(x.visitedDate.astimezone().second)
        date = str(x.visitedDate.date()) + " " + hr + ":" + min + ":" + sec
        visitList.append(date)
        location = str(x.city) + ", " + str(x.region) + ", " + str(x.country)
        locationList.append(location)

    for y in verificationTable:
        passwordList.append(y.password)
        passwordID.append(y.shortCode.pk)

    dumpIPlist = dumps(iplist)
    dumpIDlist = dumps(idlist)
    dumpVisitList = dumps(visitList)
    dumpPasswordList = dumps(passwordList)
    dumpPasswordID = dumps(passwordID)
    dumpLocationList = dumps(locationList)

    context = {
        'object_list': queryset,
        'ipset_list': ipset,
        'verifiedlist': verificationTable,
        'hostname': host,
        'iplist': dumpIPlist,
        'idlist': dumpIDlist,
        'visitlist': dumpVisitList,
        'passwordlist': dumpPasswordList,
        'passwordIDlist': dumpPasswordID,
        'locationList': dumpLocationList,
    }
    return render(request, 'manage.html', context)


@login_required(login_url='login')
def search_view(request):
    if request.method == 'POST':
        word = request.POST['keyword']
        queryset = Url.objects.filter(longLink__icontains=word)
        context = {
            'object_list': queryset
        }
        html = render_to_string('search_result.html', context)
        return JsonResponse(html, safe=False)


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@login_required(login_url='login')
def manage_view_delete(request, pk, *args, **kwargs):
    if is_ajax(request):
        obj = Url.objects.get(pk=pk)
        obj.delete()
        return JsonResponse({"message": "success"})
    return JsonResponse({"message": "Something is wrong"})


def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Username or Password incorrect')
            return redirect('login')
    context = {}
    return render(request, 'login.html', context)


@login_required(login_url='login')
def logoutUser(request):
    logout(request)
    return redirect('login')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required(login_url='login')
def get_status(request, pk):
    try:
        longUrl = Url.objects.get(pk=pk)
        s = longUrl.status
        r = requests.head(longUrl.longLink)
        status_code = r.status_code
        if (status_code == 200):
            longUrl.status = "Good"
            longUrl.save()
            return HttpResponse("Good")
        else:
            longUrl.status = "Bad"
            longUrl.save()
            return HttpResponse("Bad")
    except requests.RequestException:
        longUrl.status = "No Server"
        longUrl.save()
        return HttpResponse("No Server")


def verification(request):
    pk = request.POST['shortcode']
    pw = request.POST['password']
    linkObj = Url.objects.get(shortCode=pk)
    veriPw = (Verification_Table.objects.get(shortCode=linkObj)).password
    if pw == veriPw:
        linkObj.clicks += 1
        ip = get_client_ip(request)
        response = requests.get(f'https://ipapi.co/{ip}/json/').json()
        city = response.get('city')
        region = response.get('region')
        country = response.get('country')
        longitude = response.get('longitude')
        latitude = response.get('latitude')
        ip_origin = IP_Adresses(shortCode=linkObj, ip_address=ip, city=city, region=region, country=country,
                                longitude=longitude,
                                latitude=latitude)
        linkObj.save()
        ip_origin.save()
        return HttpResponse(linkObj.longLink)
    else:
        return HttpResponse("wrong")


@login_required(login_url='login')
def analytics(request):
    labels = []
    data = []
    goodCount = 0
    badCount = 0
    pendingCount = 0
    longitude = []
    latitude = []
    barlabel = ['Good', 'Pending', 'Bad']

    queryset = Url.objects.all()
    q2 = IP_Adresses.objects.all()
    for chartData in queryset:
        labels.append(chartData.longLink)
        data.append(chartData.clicks)

        if chartData.status == 'Good':
            goodCount += 1
        elif chartData.status == 'Pending':
            pendingCount += 1
        else:
            badCount += 1

    bardata = [goodCount, pendingCount, badCount]

    for ipinfo in q2:
        long = str(ipinfo.longitude)
        longitude.append(long)
        lat = str(ipinfo.latitude)
        latitude.append(lat)

    dumpLong = dumps(longitude)
    dumpLat = dumps(latitude)

    context = {
        'labels': labels,
        'data': data,
        'barlabels': barlabel,
        'bardata': bardata,
        'longitude': dumpLong,
        'latitude': dumpLat

    }

    return render(request, 'analytics.html', context)