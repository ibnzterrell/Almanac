import requests
from bs4 import BeautifulSoup
import re
import datetime
import time
from requests.api import get
import pandas as pd
import calendar

list_re = re.compile("^(0?AD )?\d{1,4} (.+ )?–")
event_re  = re.compile("^(0?AD \d+|\d+ BC|\d+) – (.+\.)(\[\d+\])?$")
bc_ad_re = re.compile("^(0?AD \d+|\d+ BC)")

def isNotBC_AD(str):
    match = bc_ad_re.match(str)
    return match is None

missed_events = []
missed_dates = []
def extractEvents(month, day, event_list):
    events = []
    dates = []
    for e in event_list:
        match = event_re.match(e)
        if match is None:
            print("NO MATCH: ", e)
            missed_events.append(e)
            missed_dates.append(f"{month}-{day}")
            continue
        year = match.group(1)
        event = match.group(2)
        date = datetime.date(int(year), month, day)
        dates.append(date)
        events.append(event)
    df = pd.DataFrame()
    df["date"] = pd.Series(dates)
    df["event"] = pd.Series(events)

    return df

def getDayData(month, day):
    month_name = calendar.month_name[month]

    day_page = requests.get(f"https://en.wikipedia.org/wiki/{month_name}_{day}")

    day_soup = BeautifulSoup(day_page.content, 'html.parser')

    day_html = list(day_soup.children)[2]
    day_body = list(day_html.children)[3]
    day_lists = day_body.find_all('ul')

    day_event_lists = []
    day_matches = []
    day_mismatches  = []
    for l in day_lists:
        m = list_re.match(l.get_text())

        sub_list = l.find_all('li')
        if (m):
            day_event_lists.append(l)
            day_matches.append(sub_list[0].get_text())
        else:
            if (len(sub_list) > 0):
                day_mismatches.append(sub_list[0].get_text())
    
    day_matches = pd.Series(day_matches)
    day_mismatches = pd.Series(day_mismatches)
    print("List Matches:")
    print(day_matches)

    day_events = []
    day_births = []
    day_deaths = []

    if (len(day_event_lists) == 9):
        day_events = [e.get_text() for l in day_event_lists[0:3] for e in l.find_all('li')]
        day_births = [e.get_text() for l in day_event_lists[3:6] for e in l.find_all('li')]
        day_deaths = [e.get_text() for l in day_event_lists[6:9] for e in l.find_all('li')]
    elif (len(day_event_lists) == 3):
        day_events = [e.get_text() for e in day_event_lists[0].find_all('li')]
        day_births = [e.get_text() for e in day_event_lists[1].find_all('li')]
        day_deaths = [e.get_text() for e in day_event_lists[2].find_all('li')]
    elif (len(day_event_lists) == 12):
        # Feb 18th
        day_events = [e.get_text() for l in day_event_lists[0:4] for e in l.find_all('li')]
        day_births = [e.get_text() for l in day_event_lists[4:8] for e in l.find_all('li')]
        day_deaths = [e.get_text() for l in day_event_lists[8:12] for e in l.find_all('li')]
    elif (len(day_event_lists) == 11):
        # Feb 25th
        day_events = [e.get_text() for e in day_event_lists[0].find_all('li')]
        day_births = [e.get_text() for l in day_event_lists[1:6] for e in l.find_all('li')]
        day_deaths = [e.get_text() for l in day_event_lists[6:11] for e in l.find_all('li')]
    else:
        print(len(day_event_lists))
        print(day_mismatches)
        raise Exception("Unknown Day List Format")

    day_events = [e for e in filter(isNotBC_AD, day_events)]

    day_df = extractEvents(month, day, day_events)
    return day_df

date = datetime.date(2020, 1, 1)
stop_date = datetime.date(2021, 1, 1)
# NOTE we use 2020 because it is a leap year!

data = []

while date != stop_date:
    month = date.month
    day = date.day
    print(f"{month}-{day}")
    day_data = getDayData(month, day)
    print(day_data)
    data.append(day_data)

    date = date + datetime.timedelta(days=1)
    time.sleep(6)

data = pd.concat(data)
data = data.sort_values(by=["date"])
data.to_csv("./data/WikipediaEvents.csv", index=False)
missed_events = pd.Series(missed_events)
missed_dates = pd.Series(missed_dates)
missed = pd.DataFrame()
missed["date"] = missed_dates
missed["event"] = missed_events
missed.to_csv("./data/wikipediaMissed.csv", index=False)