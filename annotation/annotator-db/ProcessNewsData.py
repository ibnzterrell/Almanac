import time
import pandas as pd
import json
import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

startMonth = int(os.getenv("START_MONTH"))
startYear = int(os.getenv("START_YEAR"))

yesterday = datetime.today() - timedelta(days=1)
endMonth = yesterday.month
endYear = yesterday.year

def processMonthDataframe(month, year):
    print(f"Loading {year}-{month}")

    data = {}
    with open(f"./data/raw/{year}_{month}.json", "r") as inFile:
        data = json.load(inFile)

    print("Loaded. Processing Month.")

    # Convert JSON to Dataframe
    df = pd.json_normalize(data["response"]["docs"])

    # If data is missing stop processing
    if df.empty:
        raise Exception(f"Missing Month: {year}-{month}")

    # Drop Non-Articles
    df = df[df["document_type"] == "article"]

    # Rename and Grab Columns We Want
    df["main_headline"] = df["headline.main"]
    df["print_headline"] = df["headline.print_headline"]

    # Split Keywords by Type
    df["people"] = [json.dumps([obj["value"] for obj in kwlist if obj["name"] == "persons"])
                    for kwlist in df["keywords"]]
    df["organizations"] = [json.dumps([obj["value"] for obj in kwlist if obj["name"]
                                       == "organizations"]) for kwlist in df["keywords"]]
    df["subjects"] = [json.dumps([obj["value"] for obj in kwlist if obj["name"] == "subject"])
                      for kwlist in df["keywords"]]
    df["locations"] = [json.dumps([obj["value"] for obj in kwlist if obj["name"]
                                   == "glocations"]) for kwlist in df["keywords"]]

    df = df[["uri", "pub_date", "type_of_material", "main_headline",
             "print_headline", "abstract", "snippet", "lead_paragraph", "news_desk", "section_name", "web_url", "people", "organizations", "subjects", "locations"]]

    # Drop Invalid Dates
    df["pub_date"] = pd.to_datetime(df["pub_date"], errors="coerce")
    df = df.dropna(subset=["pub_date"])

    # Drop Unlabeled Material
    df = df.dropna(subset=["type_of_material"])

    # Drop Non-News Material
    df = df[df["type_of_material"].isin(
        ["Archives", "News", "Brief", "Obituary", "Obituary (Obit)"])]

    # Drop Media News Desks that aren't text articles
    df = df[~df['news_desk'].isin(["Podcasts"])]

    # Drop Single Word Headlines
    df = df[df["main_headline"].str.contains(" ")]

    # Drop Missing Titles
    df = df[~df["main_headline"].str.contains("No Title")]
    
    # Drop Duplicates
    df = df.drop_duplicates(subset=["uri"], keep="first")
    df = df.drop_duplicates(subset=["main_headline"], keep=False)

    # Visual Sanity Check
    print(df[["pub_date", "main_headline"]])
    return df


dfs = []


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


for month, year in month_year_range(startMonth, startYear, endMonth, endYear):
    mdf = processMonthDataframe(month, year)
    if (not mdf.empty):
        dfs.append(mdf)

print("Concatenating")
dfs = pd.concat(dfs)
# The NYT API tends to return duplicates
print("Dropping Duplicates")
dfs = dfs.drop_duplicates(subset=["uri"], keep="first")
dfs = dfs.drop_duplicates(subset=["main_headline"], keep=False)
print(dfs)
print("Sections: ")
print(dfs["section_name"].unique())
print("News Desks:")
print(dfs["news_desk"].unique())
print(dfs.describe())
print("Writing to Parquet")
dfs.to_parquet(
    f"./data/NYT_Data_Clean_{startMonth}_{startYear}_to_{endMonth}_{endYear}.parquet", index=False)
