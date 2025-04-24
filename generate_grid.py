import json
from time import strftime, localtime
import datetime

import requests

URL = 'URL'

def get_epg_info():
    r = requests.get(URL)
    return r.json()

def sane_time(epoch):
    strtime = strftime("%Y%m%d%H%M%S", localtime(epoch))
    return datetime.datetime.strptime(strtime, "%Y%m%d%H%M%S")

def convert_epg_info(epg_info):
    epgd = {}
    print(len(epg_info["entries"]))
    for entry in epg_info['entries']:
        channel = entry['channelName']
        startt = sane_time(entry['start'])
        endt = sane_time(entry['stop'])
        epgd.setdefault(channel, {}).setdefault(startt, {})
        epgd[channel][startt] = {"title":entry.get('title', ""), 
                                 "subtitle":entry.get('subtitle', ""), 
                                 "desc":entry.get('description', ""), "end":endt}
    for channel, progs in epgd.items():
        if "DANIEL" in channel:
            for start in progs:
                print(channel, start, 
                      (datetime.datetime.now()-start).seconds, 
                      (progs[start]["end"]-start).seconds,
                      progs[start]["end"], 
                      progs[start]["desc"])

    return epgd

def is_running(program, starttime):
    ran = (datetime.datetime.now()-starttime).seconds
    length = (program["end"]-starttime).seconds
    if length - ran > 0:
        return 1
    return 0

def nextHoursHtml(epgd, hours = 3):
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

if __name__ == "__main__":
    grab = get_epg_info()
    epgd = convert_epg_info(grab)
    nextHoursHtml(epgd)
