import pandas as pd
import json
from datetime import timedelta
from model.DB import personEventQuery, topicEventQuery, textEventQuery, orgEventQuery

def findPersonEvents(name, events, dateField, granularity):
    df = personEventQuery(name)
    return findEvents(df, events, dateField, granularity)

def findTopicEvents(topic, events, dateField, granularity):
    df = topicEventQuery(topic)
    return findEvents(df, events, dateField, granularity)

def findTextEvents(text, events, dateField, granularity):
    df = textEventQuery(text)
    return findRelevantEvents(df, events, dateField, granularity)

def findOrgEvents(org, events, dateField, granularity):
    df = orgEventQuery(org)
    return findEvents(df, events, dateField, granularity)

granularityToPeriod = {
    "month": "M",
    "week": "W",
    "day": "D"
}

def findEvents(df, events, dateField, granularity):

    period = granularityToPeriod[granularity]

    # Cut dates to granularity specified
    df['date_period'] = pd.to_datetime(df['pub_date']).dt.to_period(period)
    events["date_period"] = pd.to_datetime(events[dateField]).dt.to_period(period)
    df = df[df["date_period"].isin(events["date_period"])]
    
    df = df[["pub_date", "date_period", "main_headline", "lead_paragraph",  "abstract", "web_url"]]

    dfh = pd.DataFrame()
    alternates = True
    if (alternates):
        dfh = df
        dfh["alternate"] = dfh.duplicated(subset=["date_period"], keep="first")
    else:
        # If multiple articles keep most recent one - most likely to have most information
        # NOTE NLP temporal / volume-based event detection should help with which article to use later on
        dfh = df.drop_duplicates(subset=["date_period"], keep="last")

    dfh = pd.merge(dfh, events, on="date_period")

    #df = df.drop(columns=["date_period"])
    return dfh

granularityToCutoffDeltaHours= {
    "month": 24,
    "week": 12,
    "day": 4,
}

def findRelevantEvents(df, events, dateField, granularity):
    period = granularityToPeriod[granularity]

    cutoffDeltaHours  = granularityToCutoffDeltaHours[granularity]
    
    # Cut dates to granularity specified
    df["pub_date_delta"] = pd.to_datetime(df["pub_date"]) + timedelta(hours=cutoffDeltaHours)
    df["date_period"] = df["pub_date_delta"].dt.to_period(period)
    events["date_period"] = pd.to_datetime(events[dateField]).dt.to_period(period)
    
    df = df[df["date_period"].isin(events["date_period"])]
    
    df = df[["pub_date", "date_period", "main_headline", "lead_paragraph",  "abstract", "web_url", "relevance"]]

    dfh = pd.DataFrame()
    alternates = True
    if (alternates):
        dfh = df
        dfh["alternate"] = dfh.duplicated(subset=["date_period"], keep="first")
    else:
        # If multiple articles in a period, keep the first one (articles are sorted highest relevance first)
        dfh = df.drop_duplicates(subset=["date_period"], keep="first")

    dfh = pd.merge(dfh, events, on="date_period")

    return dfh
  
def headline_query(data):
    events = pd.DataFrame.from_records(data["data"])
    dateField = data["date"]
    granularity = data["granularity"]

    df = pd.DataFrame()

    methodToFindEvents = {
        "person": findPersonEvents,
        "topic": findTopicEvents,
        "text": findTextEvents,
        "org": findOrgEvents
    }

    findEventsMethod = methodToFindEvents[data["method"]]
    
    df = findEventsMethod(data["tag"], events, dateField, granularity)
    
    df["date_period"] = df["date_period"].astype(str)

    headlines = json.loads(df[df["alternate"] == False].to_json(orient="records"))
    alternates = json.loads(df[df["alternate"] == True].to_json(orient="records"))

    res_data = { "headlines": headlines, "alternates": alternates}

    return json.dumps(res_data)
