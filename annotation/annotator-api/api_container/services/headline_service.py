import pandas as pd
import json
from model.DB import personEventQuery, topicEventQuery, textEventQuery, orgEventQuery
from model.NLP import getNLP, wordFilter
from model.Options import Granularity, HeadlineSearch, WordConsolidation
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

granularityToPandasPeriod = {
    Granularity.month: "M",
    Granularity.week: "W",
    Granularity.day: "D"
}

def findEvents(df, events, dateField, granularity):

    period = granularityToPandasPeriod[granularity]

    # Cut dates to granularity specified
    df['date_period'] = pd.to_datetime(df['pub_date']).dt.to_period(period)
    events["date_period"] = pd.to_datetime(events[dateField]).dt.to_period(period)
    df = df[df["date_period"].isin(events["date_period"])]
    
    df = df[["pub_date", "date_period", "main_headline", "lead_paragraph", "web_url"]]

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

def findRelevantEvents(df, events, dateField, granularity):
    period = granularityToPandasPeriod[granularity]

    # Cut dates to granularity specified
    df["date_period"] = df["pub_date"].dt.to_period(period)
    events["date_period"] = pd.to_datetime(events[dateField]).dt.to_period(period)
    
    df = df[df["date_period"].isin(events["date_period"])]
    
    df = df[["pub_date", "date_period", "main_headline", "lead_paragraph", "web_url", "relevance"]]

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

def headline_query(db, pipes, data: list[dict], granularity: str, dateField: str, query: str, options: dict):
    data = pd.DataFrame.from_records(data)
    
    return headline_cluster(db, pipes, data, granularity, dateField, query, options)

def findClusters(df, pipes, events, dateField, granularity, options):
    nlp = getNLP(pipes, options)

    period = granularityToPandasPeriod[granularity]

    df['date_period'] = pd.to_datetime(df['pub_date']).dt.to_period(period)
    events["date_period"] = pd.to_datetime(events[dateField]).dt.to_period(period)
    df = df[df["date_period"].isin(events["date_period"])]
    
    df = df[["pub_date", "date_period", "main_headline", "lead_paragraph", "web_url"]]
    
    date_periods = pd.unique(df["date_period"])

    match options["scoringSpace"]:
        case HeadlineSearch.headline:
            df["doc"] = df["main_headline"]
        case HeadlineSearch.headlinewithlead:
            df["doc"] = df["main_headline"] + " " + df["lead_paragraph"]

    df["doc"] = df["doc"].str.lower()
    df["doc"] = list(nlp.pipe(df["doc"]))

    all_words = [token.lemma_ for doc in df["doc"] for token in doc if wordFilter(token, options["alphaFilter"])]

    dictionary = sorted(set(all_words))

    # Term Frequencies
    fs = []
    trfs = []
    trfirfs = []

    if (options["singleDocumentFilter"]):
        wordsets = []
        for dp in date_periods:
            docwordsets = []
            for doc in df[df["date_period"] == dp]["doc"]:
                docwordset = set([token.lemma_ for token in doc if wordFilter(token, options["alphaFilter"])])
                docwordsets.append(docwordset)
            rangewords = [word for docset in docwordsets for word in docset]
            wordsets.append(set(rangewords))
        dictionary = sorted(set([word for wordset in wordsets for word in wordset]))

    # Calculate Range Term Frequencies
    for dp in date_periods:
        words = []
        if (options["booleanFrequencies"]):
            docwordsets = []
            for doc in df[df["date_period"] == dp]["doc"]:
                docwordset = set([token.lemma_ for token in doc if wordFilter(token, options["alphaFilter"])])
                docwordsets.append(docwordset)
            words = [word for docset in docwordsets for word in docset]
        else:
            words = [token.lemma_ for doc in df[df["date_period"] == dp]["doc"] for token in doc if wordFilter(token, options["alphaFilter"])]
        fc = Counter(words)

        f = {w: fc.get(w, 0) for w in dictionary}
        fs.append(f)
        trf = {w: f.get(w, 0) / len(words) for w in dictionary}
        trfs.append(trf)
    
    N = len(date_periods)

    # Calculate Range Frequencies
    rf = {w: sum([1 if (f.get(w, 0) > 0) else 0 for f in fs]) for w in dictionary}

    #Calculate Inverse Range Frequencies
    irf = {w: 1 + math.log(N / (1 + rf[w])) for w in dictionary}    

    # Calculate TRF-IRFs
    for trf in trfs:
        trfirf = {w: trf[w] * irf[w] for w in dictionary}

        if (options["decayWeighting"]):
            # Apply Exponential Decay Weighting
            trfsorted = sorted(trfirf.items(), key =
                lambda kv : kv[1], reverse=True)
            trfirf = {k: v * pow(0.80, i) for (i, (k, v)) in enumerate(trfsorted, 0)}

        trfirfs.append(trfirf)

    topks = []

    for (f, trf, trfirf) in zip(fs, trfs, trfirfs):
        topk = heapq.nlargest(25, trf, key=trfirf.get)
        topk = {w: {"f": f.get(w, 0), "trf": trf.get(w, 0), "irf": irf.get(w, 0), "rf":rf.get(w, 0), "trfirf": trfirf.get(w, 0)} for w in topk}
        topks.append(topk)

    dptopKs = {str(dp) : topktrfirf for (dp, topktrfirf) in zip(date_periods, topks)}
    
    trfDateLookup = {dp : trf for (dp, trf) in zip (date_periods, fs)}

    df["score"] = scoreDocs(df["doc"], df["date_period"], trfDateLookup, options)

    df = df.sort_values(by="score", ascending=False)

    df["alternate"] = df.duplicated(subset=["date_period"], keep="first")
    df = pd.merge(df, events, on="date_period")
    
    return (df, dptopKs)


def headline_cluster(db, pipes, events, granularity, dateField, query, options):
    df = textEventQuery(db, query, options)

    (df, dptopKs) = findClusters(df, pipes, events, dateField, granularity, options)

    df["date_period"] = df["date_period"].astype(str)
    # print(df)

    df = df.loc[:, ~df.columns.isin(["doc"])]

    headlines = json.loads(df[df["alternate"] == False].to_json(orient="records"))

    res_data = { "headlines": headlines}

    if (options["alternates"]):
        res_data["alternates"] = json.loads(df[df["alternate"] == True].to_json(orient="records"))

    if (options["topK"]):
        res_data["topK"] = dptopKs

    return res_data

def scoreDocs(docs, date_periods, trfLookup, options):
    scores = []
    for (d, dp) in zip(docs, date_periods):
        words = [token.lemma_ for token in d if wordFilter(token, options["alphaFilter"])]
        words = set(words)
        score = sum([trfLookup[dp].get(w, 0) for w in words])
        scores.append(score)

    return scores