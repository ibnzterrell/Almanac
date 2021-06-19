import json
import pandas as pd
from flask import Flask, request, g
from flask_cors import CORS, cross_origin
import sqlalchemy as sa
import re
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

def db_connect():
    db = getattr(g, '_database', None)
    articleTable = getattr(g, '_articleTable', None)
    personTable = getattr(g, '_personTable', None)
    personTagTable = getattr(g, '_personTagTable', None)
    organizationTable = getattr(g, '_organizationTable', None)
    organizationTagTable = getattr(g, '_organizationTagTable', None)
    engine = getattr(g, '_engine', None)

    if engine is None:
        engine = g._engine = sa.create_engine(
            os.getenv("SQL_ENGINE"), echo=True)
    
    if db is None:
        db = g._database = engine.connect()

    if articleTable is None:
        md = sa.MetaData()
        md.reflect(bind=engine)
        articleTable = g.__articleTable = md.tables["article"]

    if personTable is None:
        personTable = g.__personTable = md.tables["person"]

    if personTagTable is None:
        personTagTable = g.__personTagTable = md.tables["person_tag"]

    if organizationTable is None:
        organizationTable = g.__organizationTable = md.tables["organization"]

    if organizationTagTable is None:
        organizationTagTable = g.__organizationTagTable = md.tables["organization_tag"]

    return (db, articleTable, personTable, personTagTable, organizationTable, organizationTagTable)


def legalize(name):
    # Convert common name to legal name for NYT lookup
    return {
        "joe biden": "Joseph R Jr Biden",
        "bernie sanders": "Bernard Sanders",
        "jack welch": "John F Jr Welch"
    }.get(name, name)  # Return name if not found


def convertNameForNYT(name):
    name = legalize(name)

    # Convert name from Cable TV format (first middle last) to NYT format (last, first middle)
    results = re.search("(.*) (.*)", name).groups()

    # Certain names from the NYT do not use comma notation (Chinese mostly)
    if name in ["xi jinping"]:
        return name

    return f"{results[1]}, {results[0]}"

def findPerson(name):
    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

    joinPersonTag = sa.sql.join(personTable, personTagTable, personTable.c.personId == personTagTable.c.personId)

    sqlQuery = sa.sql.select([personTable.c.person, sa.func.count().label("articleCount")]).select_from(joinPersonTag).where(personTable.c.person.like(f"{name}%")).group_by(personTable.c.person).order_by(sa.desc("articleCount"))
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)

    return df

# def findTopic(topic):
#     (db_conn, articleTable, personTable, personTagTable) = db_connect()
#     sqlQuery = sa.sql.select([personTable.c.person]).select_from(personTable).where(personTable.c.person.ilike(f"{topic}%"))
#     df = pd.read_sql_query(sql=sqlQuery, con=db_conn)

#     return df

def findOrg(org):
    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

    joinOrgTag = sa.sql.join(organizationTable, organizationTagTable, organizationTable.c.organizationId == organizationTagTable.c.organizationId)

    sqlQuery = sa.sql.select([organizationTable.c.organization, sa.func.count().label("articleCount")]).select_from(joinOrgTag).where(organizationTable.c.organization.like(f"{org}%")).group_by(organizationTable.c.organization).order_by(sa.desc("articleCount"))
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)

    return df

def findPersonEvents(name, events, dateField, granularity):
    # name = convertNameForNYT(name)
    df = []

    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

    joinPersonTag = sa.sql.join(
        personTable, personTagTable, personTable.c.personId == personTagTable.c.personId)

    joinPersonTagArticle = sa.sql.join(
        articleTable, joinPersonTag, articleTable.c.articleId == personTagTable.c.articleId)

    # Tags are ordered by relevance, only select articles where they are first or second person listed
    sqlQuery = sa.sql.select([articleTable.c.main_headline,
                              articleTable.c.pub_date, articleTable.c.lead_paragraph, articleTable.c.abstract, articleTable.c.web_url]).select_from(joinPersonTagArticle).where(personTable.c.person == name).where(personTagTable.c.rank <= 2)

    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    return findEvents(df, events, dateField, granularity)


def findTopicEvents(topic, events, dateField, granularity):
    df = []

    (db_conn, articleTable) = db_connect()

    # Tags are ordered by relevance, only select articles where they are first person listed
    sqlQuery = sa.sql.select([articleTable.c.main_headline, articleTable.c.pub_date, articleTable.c.lead_paragraph, articleTable.c.abstract, articleTable.c.web_url]).where(
        articleTable.c.subjects.ilike(f"[\'{topic}%"))
    # NOTE While fairly limiting, we use SQLAlchemy selectables instead of raw queries to prevent SQL injection

    # TODO Make more efficient by doing processing ahead of time to offload date filtering to DB
    # TODO Make more accurate using Heideltime NLP to temporalize events
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    return findEvents(df, events, dateField, granularity)


def findTextEvents(text, events, dateField, granularity):
    df = []

    (db_conn, articleTable) = db_connect()

    # Tags are ordered by relevance, only select articles where they are first person listed

    sqlQuery = sa.sql.select([articleTable.c.main_headline, articleTable.c.pub_date, articleTable.c.lead_paragraph, articleTable.c.abstract, articleTable.c.web_url]).where(
        articleTable.c.main_headline.ilike(f"%{text}%"))

    # TODO Make more efficient by doing processing ahead of time to offload date filtering to DB
    # TODO Make more accurate using Heideltime NLP to temporalize events
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    return findEvents(df, events, dateField, granularity)


def findOrgEvents(org, events, dateField, granularity):
    df = []

    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

    joinOrgTag = sa.sql.join(
        organizationTable, organizationTagTable, organizationTable.c.organizationId == organizationTagTable.c.organizationId)

    joinOrgTagArticle = sa.sql.join(
        joinOrgTag, articleTable, organizationTagTable.c.articleId == articleTable.c.articleId)

    # Tags are ordered by relevance, only select articles where they are first or second person listed
    sqlQuery = sa.sql.select([articleTable.c.main_headline,
                              articleTable.c.pub_date, articleTable.c.lead_paragraph, articleTable.c.abstract, articleTable.c.web_url]).select_from(joinOrgTagArticle).where(organizationTable.c.organization == org).where(organizationTagTable.c.rank <= 1)

    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    return findEvents(df, events, dateField, granularity)


def findEvents(df, events, dateField, granularity):
    granularityToPeriod = {
        "month": "M",
        "week": "W",
        "day": "D"
    }
    period = granularityToPeriod[granularity]

    # Cut dates to granularity specified
    df['period_date'] = pd.to_datetime(df['pub_date']).dt.to_period(period)
    events["period_date"] = pd.to_datetime(events[dateField]).dt.to_period(period)
    df = df[df["period_date"].isin(events["period_date"])]

    print(df)
    
    print(df['period_date'])
    print(events["period_date"])

    print(events)
    print(df)

    # If multiple articles keep most recent one - most likely to have most information
    # NOTE NLP temporal / volume-based event detection should help with which article to use later on
    df = df.drop_duplicates(subset=["period_date"], keep="last")
    df = df[["pub_date", "period_date", "main_headline", "lead_paragraph",  "abstract", "web_url"]]
    df = pd.merge(df, events, on="period_date")
    df = df.drop(columns=["period_date"])
    return df



@app.route("/search/<tagType>/<query>", methods=["GET"])
def searchRoute(tagType, query):

    df = []
    if (tagType == "person"):
        df = findPerson(query)
    # elif (tagType == "topic"):
    #     df = findTopic(query)
    elif (tagType == "org"):
        df = findOrg(query)

    return df.to_json(orient='records')


@app.route("/headlines", methods=["POST"])
def eventsRoute():
    data = json.loads(request.data)
    print(data)
    events = pd.DataFrame.from_records(data["data"])
    dateField = data["date"]
    granularity = data["granularity"]

    df = pd.DataFrame()
    if (data["method"] == "person"):
        df = findPersonEvents(data["tag"], events, dateField, granularity)
    elif (data["method"] == "topic"):
        df = findTopicEvents(data["tag"], events, dateField, granularity)
    elif (data["method"] == "text"):
        df = findTextEvents(data["tag"], events, dateField, granularity)
    elif (data["method"] == "org"):
        df = findOrgEvents(data["tag"], events, dateField, granularity)

    return df.to_json(orient='records')


@app.route("/warmup", methods=["GET"])
def warmupRoute(name):
    db_connect()
    return "OK"

# Close database on shutdown
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(port=3030)
