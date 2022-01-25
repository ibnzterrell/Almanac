import pandas as pd
import json
from datetime import timedelta
from model.DB import personEventQuery, topicEventQuery, textEventQuery, orgEventQuery
from model.NLP import loadNLP
from collections import Counter
import heapq
import math

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

def findClusters(df, events, dateField, granularity):
    nlp = loadNLP()

    period = granularityToPeriod[granularity]

    df['date_period'] = pd.to_datetime(df['pub_date']).dt.to_period(period)
    events["date_period"] = pd.to_datetime(events[dateField]).dt.to_period(period)
    df = df[df["date_period"].isin(events["date_period"])]
    
    df = df[["pub_date", "date_period", "main_headline", "lead_paragraph",  "abstract", "web_url"]]
    
    date_periods = pd.unique(df["date_period"])

    df["doc"] = df["main_headline"] + " " + df["lead_paragraph"]
    df["doc"] = df["doc"].str.lower()

    df["hdoc"] = df["main_headline"]
    df["hdoc"] = df["hdoc"].str.lower()

    df["doc"] = list(nlp.pipe(df["doc"]))
    df["hdoc"] = list(nlp.pipe(df["hdoc"]))

    all_words = [token.lemma_ for doc in df["doc"] for token in doc if not (token.is_stop or token.is_punct)]

    dictionary = sorted(set(all_words))

    total_tf = Counter(all_words)
    #print(tdf)

    # Range Term Frequencies
    tfs = []
    # Inverse Range Frequencies
    irfs = []
    # Range Words
    rwords = []

    tfirfs = []

    # Calculate Range Term Frequencies
    for dp in date_periods:
        words = [token.lemma_ for doc in df[df["date_period"] == dp]["doc"] for token in doc if not (token.is_stop or token.is_punct)]
        f = Counter(words)
        tf = {w: f.get(w, 0) / len(words) for w in dictionary}
        tfs.append(tf)
        rwords.append(words)
    
    N = len(date_periods)

    # Calculate Range Frequencies
    rf = {w: sum([1 if (tf[w] > 0) else 0 for tf in tfs]) for w in dictionary}

    #Calculate Inverse Range Frequencies
    irf = {w: math.log(N / (1 + rf[w])) for w in dictionary}    

    # Calculate TF-IRFs
    for tf in tfs:
        tfirf = {w: tf[w] * irf[w] for w in dictionary}
        tfirfs.append(tfirf)

    for (dp, tfirf) in zip(date_periods, tfirfs):
        print(dp)
        topk = heapq.nlargest(25, tf, key=tfirf.get)
        topktfirf = [tfirf[w] for w in topk]
        print(topk)
        print(topktfirf)
    
    tfDateLookup = {dp : tf for (dp, tf) in zip (date_periods, tfs)}

    df["score"] = scoreDocs(df["doc"], df["date_period"], tfDateLookup)

    df = df.sort_values(by="score", ascending=False)

    df["alternate"] = df.duplicated(subset=["date_period"], keep="first")
    df = pd.merge(df, events, on="date_period")
    
    return df


def headline_cluster_query(data):
    events = pd.DataFrame.from_records(data["data"])
    dateField = data["date"]
    granularity = data["granularity"]

    df = textEventQuery(data["tag"])

    df = findClusters(df, events, dateField, granularity)

    df["date_period"] = df["date_period"].astype(str)
    # print(df)

    df = df.loc[:, ~df.columns.isin(["doc", "hdoc"])]

    headlines = json.loads(df[df["alternate"] == False].to_json(orient="records"))
    alternates = json.loads(df[df["alternate"] == True].to_json(orient="records"))

    res_data = { "headlines": headlines, "alternates": alternates}

    return json.dumps(res_data)

def scoreDocs(docs, date_periods, tfLookup):
    scores = []
    for (d, dp) in zip(docs, date_periods):
        words = [token.lemma_ for token in d if not (token.is_stop or token.is_punct)]
        score = sum([tfLookup[dp][w] for w in words])
        scores.append(score)

    return scores