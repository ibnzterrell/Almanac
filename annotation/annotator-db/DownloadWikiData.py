from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import requests
import json
import time

load_dotenv()

startYear = int(os.getenv("START_YEAR"))
endYear = int(os.getenv("END_YEAR"))


def saveYear(year):
    dataResponse = requests.get(f"https://en.wikipedia.org/wiki/{year}")
    yearData = (dataResponse.content).decode("utf-8")
    with open(f"./data/raw/wiki/{year}.html", "w") as outFile:
        outFile.write(yearData)


def yearExists(year):
    return os.path.exists(f"./data/raw/wiki/{year}.html")


for year in range(startYear, endYear + 1):
    print(f"Retrieving {year}:")
    if not yearExists(year):
        time.sleep(6)
        print(f"Saving {year}")
        saveYear(year)
    else:
        time.sleep(1)
        print(f"{year} already retrieved")
