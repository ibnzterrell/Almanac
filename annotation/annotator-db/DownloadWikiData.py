import requests
from bs4 import BeautifulSoup
import re
import datetime
import time
from requests.api import get
import pandas as pd
import calendar

startYear = 1980
stopYear = 2023
currentYear = startYear

data = []

months = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

day_re = re.compile("(\w+) (\d?\d) ([–-])? (.*)(\[.+\])*")


def extractEvents(year, daylist):
    dates = []
    events = []
    for day in daylist:
        # if day.find("ul"):
        # else:
        # print(day.text)
        match = day_re.match(day.text)

        if match is None:
            print("NO MATCH: ", day.text)
            continue
        month = match.group(1)
        day = match.group(2)
        event = match.group(4)

        date = datetime.date(int(year), months.index(month) + 1, int(day))
        dates.append(date)
        events.append(event)

    df = pd.DataFrame()
    df["date"] = pd.Series(dates, dtype="datetime64[ns]")
    df["event"] = pd.Series(events, dtype="string")

    return df


def getYearData(year):
    year_page = requests.get(f"https://en.wikipedia.org/wiki/{year}")
    year_soup = BeautifulSoup(year_page.content, 'html.parser')
    year_html = list(year_soup.children)[2]
    year_body = year_html.find(id="mw-content-text")
    year_content = list(year_body.children)[0]

    page_lists = year_content.findChildren('ul', recursive=False)

    year_events = []

    for ul in page_lists:
        # Only pull the Events section, which is all the <ul>s after the "Events" H2
        # Hacky, but necessary due to Wikipedia not nesting elements
        if ul.find_previous("h2").text != "Events" and ul.find_previous("h2").text != "Events[edit]":
            print("Skipping: ", ul.find_previous("h2").text)
            continue

        # if ul.find_previous("h3") and any(month in ul.find_previous("h3").text for month in months):

            # print(ul.find_previous("h3").text)
            # print(ul)
        daylist = ul.findChildren("li", recursive=False)
        # TODO - extract days that have multiple events

        events = extractEvents(year, daylist)
        year_events.append(events)

    return pd.concat(year_events)


while currentYear != stopYear + 1:
    print(f"Year: {currentYear}")
    year_data = getYearData(currentYear)
    # print(year_data)
    # print(year_data[0])
    data.append(year_data)
    currentYear = currentYear + 1
    time.sleep(6)


data = pd.concat(data)
data = data.sort_values(by=["date"])
data.to_parquet("./data/WikiEvents.parquet", index=False)
print(data)
# missed_events = pd.Series(missed_events)
# missed_dates = pd.Series(missed_dates)
# missed = pd.DataFrame()
# missed["date"] = missed_dates
# missed["event"] = missed_events
# missed.to_csv("./data/wikipediaMissed.csv", index=False)
