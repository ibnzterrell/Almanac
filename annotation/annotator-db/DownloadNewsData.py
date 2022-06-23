from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import requests
import json
import time

load_dotenv()

startMonth = int(os.getenv("START_MONTH"))
startYear = int(os.getenv("START_YEAR"))

yesterday = datetime.today() - timedelta(days=1)
endMonth = yesterday.month
endYear = yesterday.year

apiKey = os.getenv("apiKeyNYT")

def month_year_range(startMonth, startYear, endMonth, endYear):
    for year in range(startYear, endYear + 1):
        startRangeMonth = 1
        stopRangeMonth = 12 + 1

        if year == startYear:
            startRangeMonth = startMonth
        if year == endYear:
            stopRangeMonth = endMonth + 1

        for month in range(startRangeMonth, stopRangeMonth):
            yield month, year

def saveMonth(month, year):
    dataResponse = requests.get(
        f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key={apiKey}")
    monthData = json.loads(dataResponse.content)
    print(monthData)
    with open(f"./data/raw/{year}_{month}.json", "w") as outFile:
        json.dump(monthData, outFile)

def monthExists(month, year):
    return os.path.exists(f"./data/raw/{year}_{month}.json")

for month, year in month_year_range(startMonth, startYear, endMonth, endYear):
    print(f"Retrieving {year}-{month}:")
    if not monthExists(month, year):
        time.sleep(6)
        print(f"Saving {year}-{month}")
        saveMonth(month, year)
    else:
        time.sleep(1)
        print(f"{year}-{month} already retrieved")

saveMonth(endMonth, endYear)