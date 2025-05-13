import json
from time import strftime, localtime
import datetime
from flask import Flask, render_template, g
from requests.auth import HTTPBasicAuth
from datetime import datetime
from datetime import date

app = Flask(__name__)

import requests

URL = 'APIURL/api/epg/events/grid?channelTag=tv&limit=1000'

def get_epg_info():
    r = requests.get(URL)
    return r.json()

def sane_time(epoch):
    strtime = strftime("%Y%m%d%H%M%S", localtime(epoch))
    return datetime.strptime(strtime, "%Y%m%d%H%M%S")

def within_window(now, startt, endt, running, hours):
    delta = startt-now     
    if (delta.seconds >= 0 and delta.seconds < 60.0*60*hours and delta.days == 0) or running:
        return 1
    return 0

def generate_timerange(now, startt, endt):
    shortstart = date.strftime(startt, "%H:%M") 
    shortend = date.strftime(endt, "%H:%M") 
    return f'{shortstart} - {shortend} - {int((endt-now).seconds/60)}min\n'

def convert_epg_info(epg_info, hours = 3):
    now = datetime.now()
    epgd = {}

    for entry in epg_info['entries']:
        channel = entry['channelName']
        startt = sane_time(entry['start'])
        endt = sane_time(entry['stop'])
        width = int(int((endt-now).seconds)/60.0 * 10)
        description = entry.get('description', 'N/A')
        title = entry['title']

        running = is_running(now, startt, endt)
        in_window = within_window(now, startt, endt, running, hours)
        timerange = generate_timerange(now, startt, endt)

        if in_window:
            epgd.setdefault(channel, {}).setdefault(startt, {})
            epgd[channel][startt] = {
                'title': title,
                'end': endt,
                'width': width,
                'description': description,
                'running': running,
                'timerange': timerange
            }
    
    return epgd

def is_running(now, starttime, endtime):
    ran = (now-starttime).seconds
    length = (endtime-starttime).seconds
    if length - ran > 0:
        return 1
    return 0

def nextHoursHtml(epgd, hours = 5):
    """
    How to see if something happens in the next n hours? 
    timedelta.seconds / 60.0 < 60*hours
    """

    header = '<!doctype html>\n<html lang="de">\n  <head>\n <link rel="stylesheet" href="style.css">\n <meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">\n<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>\n<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>\n<title>Titel</title>\n </head>\n <body>\n'
    startlist = '<ul class="container">\n'
    endlist = '</ul>\n'
    channel_tag = "<label>{} </label>\n"
    footer = '<script>\n$(document).ready(function(){\n    $(\'[data-toggle="popover"]\').popover({placement: "auto"});\n});\n</script></body>\n</html>'
    entry = '<li class = "item", style="width: {}px"; , data-toggle="popover" title="{}" data-content="{}">{}</li>\n'
    running_entry = '<li class = "running_item", style="width: {}px"; , data-toggle="popover" title="{}" data-content="{}">{}</li>\n'
    channel_entry = '<li class = "channel", style="width: 150px";>{}</li>\n'    
    now = datetime.datetime.now()
    coll = []
    channel_names = []
    for channel in sorted(epgd):
        listor = []
        listor.append(channel)
        coi = epgd[channel]
        for startt in sorted(coi):
            delta = startt-now
            running = is_running(coi[startt], startt)
            
            
            if (delta.seconds >= 0 and delta.seconds < 60.0*60*hours and delta.days == 0) or running:
                shortstart = datetime.date.strftime(startt, "%H:%M") 
                shortend = datetime.date.strftime(coi[startt]["end"], "%H:%M") 
                timerange = f'{shortstart} - {shortend} - {int((coi[startt]["end"]-now).seconds/60)}min\n'
                listor.append([coi[startt]["title"], (coi[startt]["end"]-now).seconds, coi[startt]["desc"], timerange, running])
        content = []
        channel_names.append(channel_tag.format(channel))
        for i, l in enumerate(listor):
            
            if i == 0:
                content.append(channel_entry.format(l))
                continue
            width = int(int(l[1])/60.0 * 10)
            title = l[0]
            desc = l[3] + l[2]
            if i == 1:
                content.append(running_entry.format(width, title, desc, title))
                continue
            
            content.append(entry.format(width, title, desc, title))
        coll.append(content)
    with open("epgwall.html", "w") as o:
        o.write(header)
        for i, l in enumerate(coll):
            o.write(startlist) 
            for c in l:
                o.write(c)
            o.write(endlist)
        o.write(footer)

#if __name__ == "__main__":
#    grab = get_epg_info()
#    epgd = convert_epg_info(grab)
#    nextHoursHtml(epgd)


@app.route("/")
def index():
    try:
        params = {
            "limit": 1000,
        }
        response = requests.get(URL)
        epg_data = response.json()

    except Exception as e:
        epg_data = {"error": str(e)}
    epgd = convert_epg_info(epg_data)
        #nextHoursHtml(epgd)
    return render_template("index.html", epg=epgd)

if __name__ == "__main__":
    app.run(debug=True)

