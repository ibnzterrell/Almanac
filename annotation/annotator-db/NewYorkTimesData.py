import time
import pandas as pd
import json
import requests
from dotenv import load_dotenv
import os

# Downloads last two decades of NYT Headlines, 01/01/2000 - 12/31/2021
startMonth = 1
startYear = 2000
endMonth = 3
endYear = 2022

load_dotenv()
# 1851 oldest, newest is current day
apiKey = os.getenv("apiKeyNYT")

# python -u .\NewYorkTimesData.py


def getMonthDataframe(month, year):
    print(f"Retrieving {year}-{month}")
    rawMonthData = requests.get(
        f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key={apiKey}")
    data = json.loads(rawMonthData.content)
    print("Retrieved. Processing Month.")

    # Convert JSON to Dataframe
    df = pd.json_normalize(data["response"]["docs"])

    # Some months are missing, don't process those
    if df.empty:
        print(f"Missing Month: {year}-{month}")
        return df

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
    # df = df[["uri", "pub_date", "type_of_material", "main_headline", "print_headline", "lead_paragraph",
    #          "abstract", "keywords", "news_desk", "section_name", "subsection_name", "web_url"]]

    # NOTE: Changed due to lead_paragraph, abstract, and subsection_name missing from 2018/8 forward
    # df = df[["uri", "pub_date", "type_of_material", "main_headline",
    #          "print_headline", "snippet", "news_desk", "section_name", "web_url", "people", "organizations", "subjects", "locations"]]

    df = df[["uri", "pub_date", "type_of_material", "main_headline",
             "print_headline", "abstract", "snippet", "lead_paragraph", "news_desk", "section_name", "web_url", "people", "organizations", "subjects", "locations"]]

    # Drop Unlabeled Material
    df = df.dropna(subset=["type_of_material"])

    # Drop Non-News Material
    df = df[df["type_of_material"].isin(
        ["Archives", "News", "Brief", "Obituary", "Obituary (Obit)"])]

    # Drop News Desks that aren't event headlines
    #df = df[~df['news_desk'].isin(["BookReview", "Podcasts", "Upshot"])]

    # Drop Sections that typically aren't about singular events
    #df = df[~df["section_name"].isin(["Opinion", "Fashion & Style"])]

    # Drop Single Word Headlines
    df = df[df["main_headline"].str.contains(" ")]

    # Drop Missing Titles
    df = df[~df["main_headline"].str.contains("No Title")]
    
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

    mdf = getMonthDataframe(month, year)
    if (not mdf.empty):
        dfs.append(mdf)
        # NOTE NYT API has a rate limit of 10 requests per minute
    time.sleep(6)

print("Concatenating")
dfs = pd.concat(dfs)
# The NYT API tends to return duplicates
print("Dropping Duplicates")
dfs = dfs.drop_duplicates(subset=["uri"], keep="first")
dfs = dfs.drop_duplicates(subset=["main_headline"], keep=False)
print(dfs)
print("Writing to CSV")
dfs.to_csv(
    f"./data/NYT_Data_Raw_{startMonth}_{startYear}_to_{endMonth}_{endYear}.csv", index=False, index_label=False)
